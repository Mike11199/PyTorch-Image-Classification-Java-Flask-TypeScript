package pytorchAPI.controllers;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import pytorchAPI.services.VideoService;

import java.io.IOException;

@RestController
public class VideoController {
    private final VideoService videoService;

    public VideoController(VideoService videoService) {
        this.videoService = videoService;
    }

    @RequestMapping({"/api-java-spring-boot/video-jobs", "/api-java-spring-boot/video-jobs/**"})
    public void proxy(HttpServletRequest request, HttpServletResponse response)
            throws IOException, InterruptedException {
        videoService.forwardVideoRequest(request, response);
    }
}
