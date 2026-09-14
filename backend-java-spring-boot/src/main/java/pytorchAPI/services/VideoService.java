package pytorchAPI.services;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.List;

/** Stream video API traffic without holding uploads or playback files in memory. */
@Service
public class VideoService {
    private static final String PUBLIC_PATH = "/api-java-spring-boot/video-jobs";
    private static final List<String> REQUEST_HEADERS =
            List.of("Authorization", "Content-Type", "Range", "If-Range");
    private static final List<String> RESPONSE_HEADERS =
            List.of("Content-Type", "Content-Length", "Content-Range", "Accept-Ranges", "ETag");

    private final HttpClient client;
    private final String upstreamBase;

    public VideoService() {
        this(HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build(),
                "http://127.0.0.1:5000/api-pytorch/video-jobs");
    }

    public VideoService(HttpClient client, String upstreamBase) {
        this.client = client;
        this.upstreamBase = upstreamBase;
    }

    public void forwardVideoRequest(HttpServletRequest request, HttpServletResponse response)
            throws IOException, InterruptedException {
        HttpRequest upstreamRequest = buildUpstreamRequest(request);
        try {
            HttpResponse<InputStream> upstream = client.send(
                    upstreamRequest, HttpResponse.BodyHandlers.ofInputStream());
            copyResponse(upstream, response);
        } catch (IOException error) {
            if (response.isCommitted()) {
                throw error;
            }
            writeUnavailable(response);
        }
    }

    private URI buildUpstreamUri(HttpServletRequest request) {
        String suffix = request.getRequestURI().substring(PUBLIC_PATH.length());
        String query = request.getQueryString();
        return URI.create(upstreamBase + suffix + (query == null ? "" : "?" + query));
    }

    private HttpRequest buildUpstreamRequest(HttpServletRequest request) {
        HttpRequest.Builder builder = HttpRequest.newBuilder(buildUpstreamUri(request))
                .timeout(Duration.ofHours(1));
        copyRequestHeaders(request, builder);
        return builder.method(request.getMethod(), requestBody(request)).build();
    }

    private void copyRequestHeaders(HttpServletRequest request, HttpRequest.Builder builder) {
        for (String header : REQUEST_HEADERS) {
            String value = request.getHeader(header);
            if (value != null) {
                builder.header(header, value);
            }
        }
    }

    /** Empty start requests have no body; local video uploads use a streaming publisher. */
    private HttpRequest.BodyPublisher requestBody(HttpServletRequest request) {
        boolean hasBody = List.of("POST", "PUT", "PATCH").contains(request.getMethod())
                && request.getContentLengthLong() != 0;
        if (!hasBody) {
            return HttpRequest.BodyPublishers.noBody();
        }

        HttpRequest.BodyPublisher body = HttpRequest.BodyPublishers.ofInputStream(
                () -> openRequestStream(request));
        if (request.getContentLengthLong() > 0) {
            return HttpRequest.BodyPublishers.fromPublisher(body, request.getContentLengthLong());
        }
        return body;
    }

    private InputStream openRequestStream(HttpServletRequest request) {
        try {
            return request.getInputStream();
        } catch (IOException error) {
            throw new UncheckedIOException(error);
        }
    }

    private void copyResponse(HttpResponse<InputStream> upstream, HttpServletResponse response)
            throws IOException {
        response.setStatus(upstream.statusCode());
        for (String header : RESPONSE_HEADERS) {
            upstream.headers().firstValue(header).ifPresent(value -> response.setHeader(header, value));
        }
        response.setHeader("Cache-Control", "private, no-store");
        try (InputStream input = upstream.body()) {
            input.transferTo(response.getOutputStream());
        }
    }

    private void writeUnavailable(HttpServletResponse response) throws IOException {
        response.reset();
        response.setStatus(502);
        response.setContentType("application/json");
        response.getWriter().write(
                "{\"error\":\"The video service is unavailable. Please try again shortly.\"}");
    }
}
