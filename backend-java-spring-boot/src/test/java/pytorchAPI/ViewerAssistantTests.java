package pytorchAPI;

import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import pytorchAPI.services.VisionAssistantService;

import java.net.InetSocketAddress;
import java.net.http.HttpClient;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.*;

class ViewerAssistantTests {
    @Test
    void forwardsJsonAndPreservesBusyResponse() throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/api-pytorch/vision-assistant", exchange -> {
            String input = new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            String body = input.equals("{\"message\":\"cars orange\"}")
                    ? "{\"error\":\"busy\"}" : "{\"error\":\"wrong body\"}";
            byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(429, bytes.length);
            exchange.getResponseBody().write(bytes);
            exchange.close();
        });
        server.start();
        try {
            VisionAssistantService service = new VisionAssistantService(HttpClient.newHttpClient(),
                    "http://127.0.0.1:" + server.getAddress().getPort() + "/api-pytorch/vision-assistant");
            MockHttpServletRequest request = new MockHttpServletRequest();
            request.setContent("{\"message\":\"cars orange\"}".getBytes(StandardCharsets.UTF_8));
            MockHttpServletResponse response = new MockHttpServletResponse();
            service.forward(request, response);
            assertEquals(429, response.getStatus());
            assertEquals("{\"error\":\"busy\"}", response.getContentAsString());
        } finally {
            server.stop(0);
        }
    }

    @Test
    void rejectsLargeBodiesBeforeContactingFlask() throws Exception {
        VisionAssistantService service = new VisionAssistantService(HttpClient.newHttpClient(), "http://127.0.0.1:1");
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.setContent(new byte[16385]);
        MockHttpServletResponse response = new MockHttpServletResponse();
        service.forward(request, response);
        assertEquals(413, response.getStatus());
    }
}
