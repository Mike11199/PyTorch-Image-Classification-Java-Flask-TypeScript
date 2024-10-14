package pytorchAPI.controllers;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class Controllers {

    @GetMapping("/hello")
    public String hello() {
        return "Hello, PyTorch API!";
    }

    // Catch-all route to handle unmapped URLs
    @RequestMapping("/**")
    public String handleUnknown() {
        return "Java Spring API is running.";
    }
}