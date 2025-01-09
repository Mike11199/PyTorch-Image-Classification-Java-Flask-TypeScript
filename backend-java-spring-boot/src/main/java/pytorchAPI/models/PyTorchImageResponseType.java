package pytorchAPI.models;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

@JsonInclude(JsonInclude.Include.NON_NULL) // Exclude null fields from JSON
public class PyTorchImageResponseType {

    @JsonProperty("scores")
    private List<Double> scores;

    @JsonProperty("classes")
    private List<String> classes;

    @JsonProperty("boxes")
    private List<List<Double>> boxes;

    @JsonProperty("labels")
    private List<Integer> labels;

    @JsonProperty("masks_array")
    private List<List<List<Integer>>> masksArray;

    // Getters and Setters
    public List<Double> getScores() {
        return scores;
    }

    public List<String> getClasses() {
        return classes;
    }

    public List<List<Double>> getBoxes() {
        return boxes;
    }

    public List<Integer> getLabels() {
        return labels;
    }

    public List<List<List<Integer>>> getMasksArray() {
        return masksArray;
    }
}
