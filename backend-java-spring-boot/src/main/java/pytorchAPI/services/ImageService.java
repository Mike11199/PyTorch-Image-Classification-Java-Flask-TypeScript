package pytorchAPI.services;

import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;

import pytorchAPI.models.PyTorchImageResponseType;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Service
public class ImageService {

    private final RestTemplate restTemplate;
    private static final Logger logger = LoggerFactory.getLogger(ImageService.class);


    public ImageService() {
        this.restTemplate = new RestTemplate();
    }

    /**
     * Sends image to the specified endpoint and retrieves the response outputted by a ML model.
     *
     * @param imageFile The image file to upload.
     * @param flaskUrl  The Flask API URL to send the image to.
     * @return PyTorchImageResponseType - The response from the Flask API with bounding boxes (and optional masks).
     */
    public PyTorchImageResponseType sendImageToFlaskModel(MultipartFile imageFile, String flaskUrl)
    {

        // set headers for multipart form-data
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        // create a request body with the file added to the key "image"
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("image", imageFile.getResource());

        // create the request entity with the headers and body
        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

        logger.info("Sending image to Flask API at URL: {}", flaskUrl);

        // Send the POST request to Flask with the image
        ResponseEntity<PyTorchImageResponseType> response = restTemplate.postForEntity(
                flaskUrl,
                requestEntity,
                PyTorchImageResponseType.class
        );

        logger.info("Received response from Flask API.");

        return response.getBody();
    }
}
