package pytorchAPI.controllers;

import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.MediaType;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;

import pytorchAPI.models.PyTorchImageResponseType;


import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api-java-spring-boot")
public class ImageController {

    // POST endpoint for image file upload
    @PostMapping("/image-url-pytorch")
    public ResponseEntity<Object> analyzeImage(
            @RequestParam("image") MultipartFile imageFile) {
        if (imageFile.isEmpty()) {
            // Return 400 response if no file is provided
            Map<String, String> errorResponse = new HashMap<>();
            errorResponse.put("error", "Bad Request - Missing formData or file in the request.");
            return new ResponseEntity<>(errorResponse, HttpStatus.BAD_REQUEST);
        }

        try {
            // byte[] imageBuffer = imageFile.getBytes();

            Object response = fetchImageAnalysisUsingMultipart(imageFile);

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            Map<String, String> errorResponse = new HashMap<>();
            errorResponse.put("error", "Error reading the image file.");
            return new ResponseEntity<>(errorResponse, HttpStatus.BAD_REQUEST);
        }
    }

    public PyTorchImageResponseType fetchImageAnalysisUsingBuffer(byte[] imageBuffer) {
        try {
            RestTemplate restTemplate = new RestTemplate();

            // Set headers
            HttpHeaders headers = new HttpHeaders();
            headers.add("Content-Type", "image/jpg");

            // Create request entity
            HttpEntity<byte[]> requestEntity = new HttpEntity<>(imageBuffer, headers);

            // var modelUrl = "http://localhost:5000/api-flask-pytorch-models/image-url-pytorch";
            var modelUrl = "/api-flask-pytorch-models/image-url-pytorch";

            // Send POST request
            ResponseEntity<PyTorchImageResponseType> response = restTemplate.postForEntity(
                    modelUrl, requestEntity, PyTorchImageResponseType.class);

            // Return the response body (PyTorchImageResponseType object)
            return response.getBody();

        } catch (Exception e) {
            // Log the error and return null or handle appropriately
            System.err.println("Error: " + e.getMessage());
            return null;
        }
    }

    public PyTorchImageResponseType fetchImageAnalysisUsingMultipart(MultipartFile imageFile) {
        try {
            RestTemplate restTemplate = new RestTemplate();

            // Set headers for multipart form-data
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);

            // Create the body with the MultipartFile directly (no ByteArrayResource)
            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("image", imageFile.getResource());  // Directly using MultipartFile's getResource()

            // Create the request entity with the headers and body
            HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

            // send the POST request to Flask
            ResponseEntity<PyTorchImageResponseType> response = restTemplate.postForEntity(
                    "http://localhost:5000/api-pytorch/image-url-pytorch",
                    requestEntity,
                    PyTorchImageResponseType.class
            );


            var responseBody = response.getBody();

            if (responseBody != null && responseBody.getScores() != null) {
                System.out.println("Model Scores: " + responseBody.getScores());
                System.out.println("Model Classes: " + responseBody.getClasses());
                System.out.println("Model Boxes: " + responseBody.getBoxes());
                System.out.println("Model Labels: " + responseBody.getLabels());
            } else {
                System.out.println("Flask Response: No scores available.");
            }

            return response.getBody();

        } catch (Exception e) {
            // Log the error and return null or handle appropriately
            System.err.println("Error: " + e.getMessage());
            return null;
        }
    }
}
