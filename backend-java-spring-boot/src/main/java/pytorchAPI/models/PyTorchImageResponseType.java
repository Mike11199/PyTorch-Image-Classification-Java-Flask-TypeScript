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
    private List<List<List<Integer>>> masksArray; // Corrected Type

    // Getters and Setters

    public List<Double> getScores() {
        return scores;
    }

    public void setScores(List<Double> scores) {
        this.scores = scores;
    }

    public List<String> getClasses() {
        return classes;
    }

    public void setClasses(List<String> classes) {
        this.classes = classes;
    }

    public List<List<Double>> getBoxes() {
        return boxes;
    }

    public void setBoxes(List<List<Double>> boxes) {
        this.boxes = boxes;
    }

    public List<Integer> getLabels() {
        return labels;
    }

    public void setLabels(List<Integer> labels) {
        this.labels = labels;
    }

    public List<List<List<Integer>>> getMasksArray() {
        return masksArray;
    }

    public void setMasksArray(List<List<List<Integer>>> masksArray) {
        this.masksArray = masksArray;
    }
}
