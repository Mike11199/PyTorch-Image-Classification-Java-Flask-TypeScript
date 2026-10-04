package pytorchAPI.services;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpTimeoutException;
import java.time.Duration;

/** Keep the public Java -> Flask boundary, with bounded JSON bodies and errors. */
@Service
public class VisionAssistantService {
    private static final int MAX_REQUEST = 16384;
    private final HttpClient client;
    private final URI upstream;

    public VisionAssistantService() {
        this(HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build(),
                "http://127.0.0.1:5000/api-pytorch/vision-assistant");
    }

    public VisionAssistantService(HttpClient client, String upstream) {
        this.client = client;
        this.upstream = URI.create(upstream);
    }

    public void forward(HttpServletRequest request, HttpServletResponse response) throws IOException {
        response.setContentType("application/json");
        response.setCharacterEncoding("UTF-8");
        response.setHeader("Cache-Control", "no-store");
        byte[] body = request.getInputStream().readNBytes(MAX_REQUEST + 1);
        if (body.length > MAX_REQUEST) {
            error(response, 413, "The assistant request is too large.");
            return;
        }
        HttpRequest call = HttpRequest.newBuilder(upstream)
                .timeout(Duration.ofSeconds(300))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofByteArray(body)).build();
        try {
            HttpResponse<InputStream> result = client.send(call, HttpResponse.BodyHandlers.ofInputStream());
            try (InputStream input = result.body()) {
                byte[] payload = input.readNBytes(65537);
                if (payload.length > 65536) {
                    error(response, 502, "The assistant returned an oversized response.");
                    return;
                }
                response.setStatus(result.statusCode());
                response.getOutputStream().write(payload);
            }
        } catch (HttpTimeoutException timeout) {
            error(response, 504, "The assistant took too long. Please try again.");
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            error(response, 503, "The assistant request was interrupted.");
        } catch (IOException unavailable) {
            if (response.isCommitted()) throw unavailable;
            error(response, 502, "The assistant service is unavailable. Please try again shortly.");
        }
    }

    private void error(HttpServletResponse response, int status, String message) throws IOException {
        response.setStatus(status);
        response.getWriter().write("{\"error\":\"" + message + "\"}");
    }
}
