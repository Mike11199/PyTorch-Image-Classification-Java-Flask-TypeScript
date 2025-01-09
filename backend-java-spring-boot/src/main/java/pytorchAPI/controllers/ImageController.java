package pytorchAPI.controllers;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.util.HashMap;
import java.util.Map;

import pytorchAPI.services.ImageService;  //  abstract sending Image to Flask App
import pytorchAPI.models.PyTorchImageResponseType;


@RestController
@RequestMapping("/api-java-spring-boot")
public class ImageController {

    private final ImageService imageService;
    private static final Logger logger = LoggerFactory.getLogger(ImageService.class);

    public ImageController(ImageService imageService) {
        this.imageService = imageService;
    }

    // POST endpoint for image file upload
    @PostMapping("/image-url-pytorch")
    public ResponseEntity<Object> getFastRCNNModelResultsForImage(
            @RequestParam("image") MultipartFile imageFile) {

        // if no file is provided, return JSON message with key of "error"
        if (imageFile.isEmpty()) return getEmptyImageErrorMessage();

        try {
            String fastRCNNEndpoint = "http://localhost:5000/api-pytorch/image-url-pytorch";
            PyTorchImageResponseType response = imageService.sendImageToFlaskModel(imageFile, fastRCNNEndpoint);
            if (response == null) return getEmptyResponseError();
            printResponseBody(response);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("An error occurred while processing the image.", e);
            Map<String, String> errorResponse = new HashMap<>();
            errorResponse.put("error", "the Flask app encountered an error while processing the image.  Please try" +
                    "a smaller image file size or try again later.");
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    @PostMapping("/image-url-pytorch-mask")
    public ResponseEntity<Object> getMaskRCNNModelResultsForImage(
            @RequestParam("image") MultipartFile imageFile) {

        // if no file is provided, return JSON message with key of "error"
        if (imageFile.isEmpty()) return getEmptyImageErrorMessage();

        try {
            String maskRCNNEndpoint = "http://localhost:5000/api-pytorch/image-url-pytorch-mask";
            PyTorchImageResponseType response = imageService.sendImageToFlaskModel(imageFile, maskRCNNEndpoint);
            if (response == null) return getEmptyResponseError();
            printResponseBody(response);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("An error occurred while processing the image.", e);
            Map<String, String> errorResponse = new HashMap<>();
            errorResponse.put("error", "the Flask app encountered an error while processing the image.  Please try" +
                    "a smaller image file size or try again later.");
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * Prints Scores, Classes Boxes, Labels from model.  Does NOT print masks as these are huge
     * binary integer arrays.
     *
     * @param response The PyTorchImageResponseType from a Flask ML model.
     */
    private void printResponseBody (PyTorchImageResponseType response) {
        if (response != null && response.getScores() != null) {
            System.out.println("Model Scores: " + response.getScores());
            System.out.println("Model Classes: " + response.getClasses());
            System.out.println("Model Boxes: " + response.getBoxes());
            System.out.println("Model Labels: " + response.getLabels());
        } else {
            System.out.println("Flask Response: No scores available.");
        }
    }

    /**
     * Assembles a bad request response if a request sent to the Java App fails to include an image.
     *
     * @return An informative HTTP response using ResponseEntity of the type Bad Request.
     */
    private static ResponseEntity<Object> getEmptyImageErrorMessage() {
            Map<String, String> errorResponse = new HashMap<>();
            errorResponse.put("error", "missing formData with key 'image' or image file in the request.");
            return new ResponseEntity<>(errorResponse, HttpStatus.BAD_REQUEST);
    }

    /**
     * If an image is too large the Flask app can be sent SIGINT from the AWS EC2 instance due to running out
     * of memory.  This function returns an error if the response is empty.
     *
     * @return An informative HTTP response using ResponseEntity of the type Bad Request.
     */
    private static ResponseEntity<Object> getEmptyResponseError() {
        Map<String, String> errorResponse = new HashMap<>();
        errorResponse.put("error", "the pytorch model did not return any results.  This could occur if" +
                "the service ran out of memory on the EC2. try sending a smaller image size or try again later.");
        return new ResponseEntity<>(errorResponse, HttpStatus.BAD_REQUEST);
    }
}
