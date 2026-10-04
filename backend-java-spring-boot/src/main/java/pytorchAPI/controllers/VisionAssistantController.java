package pytorchAPI.controllers;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;
import pytorchAPI.services.VisionAssistantService;

import java.io.IOException;

@RestController
public class VisionAssistantController {
    private final VisionAssistantService service;

    public VisionAssistantController(VisionAssistantService service) {
        this.service = service;
    }

    @PostMapping("/api-java-spring-boot/vision-assistant")
    public void plan(HttpServletRequest request, HttpServletResponse response) throws IOException {
        service.forward(request, response);
    }
}
