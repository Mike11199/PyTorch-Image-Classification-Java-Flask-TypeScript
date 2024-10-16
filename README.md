# PyTorch-Image-Classification-Java-Spring-Boot-Flask-TypeScript-EC2

- Personal project involving a Java Spring Boot API, and TypeScript front end.  The API sends requests to a Flask service hosting a PyTorch fasterrcnn_resnet50_fpn_v2 computer vision model.  This is deployed on an EC2 instance with its own Route 53 domain.
- This was originally deployed on Heroku as a TypeScript/Express.js Server, using Amazon API Gateway/a lambda to send requests to a SageMaker endpoint.  I have refactored the project as this endpoint was costing roughly $50 a month.
- Can accept both an image URL or an uploaded image from one's computer.  It sends binary data to the lambda/ PyTorch Model etiher way.

- Deployed Website
  - https://machine-learning-projects.com/  - EC2 (TypeScript/ Java Spring Boot/ Flask) - NEW
  - https://pytorch-image-model-aws-app-727fe8e23222.herokuapp.com/ - Heroku/ AWS SageMaker Endpoint - OLD

- Back End Repo - AWS Endpoint/Model/etc
  - https://github.com/Mike11199/PyTorch-Image-Classification/

- Video
  - https://www.youtube.com/watch?v=abtdBPFu_yM


# EC2 Screenshots
![image](https://github.com/user-attachments/assets/a4b823e0-6bf8-4e37-b228-bfc1980449aa)
![image](https://github.com/user-attachments/assets/829c1688-adbc-4587-b18a-dc9c7c073d44)

# Website Screenshots

<br />

<img src="https://res.cloudinary.com/dwgvi9vwb/image/upload/v1703822238/cats_and_dogs_lnwfi9.png">

<br />

<img width="1659" alt="traffic_analysis" src="https://github.com/Mike11199/PyTorch-Image-Classification-TypeScript/assets/91037796/d57d26fa-45d3-4731-ae33-60b32b585d50">

<br />
<br />
<br />

<img src="https://res.cloudinary.com/dwgvi9vwb/image/upload/v1703823645/nat_geo_collage_analysis_tpnipt.png">

<br />

<img src="https://res.cloudinary.com/dwgvi9vwb/image/upload/v1703831262/winter_traffic_analysis_caxrhm.png">

<br />

<br />

<img src="https://res.cloudinary.com/dwgvi9vwb/image/upload/v1703828564/labrador_new_ogez0w.png">

<br />

