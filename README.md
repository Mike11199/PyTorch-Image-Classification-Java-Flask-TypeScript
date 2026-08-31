# Deployment

- https://machine-learning-projects.com/
  - ECS on EC2 Spot (TypeScript, Java Spring Boot, Flask/PyTorch)

## CDK Details
- Deployment is automated by [GitHub Actions](.github/workflows/deploy-cdk-aws.yml) and [AWS CDK](cdk/README.md).
- The workflow tests the CDK stack, builds three Docker images, pushes them to ECR, and deploys one ECS task containing Nginx/React, Java Spring Boot, and Flask/PyTorch.
- This is ECS on an EC2, not Fargate with ECS.

- The previous deployment required manually building and starting each service on the EC2 after git cloning, configuring Nginx, and restarting processes after updates.:
- Kept deprecated commands for set up here
  - [Java manual deployment notes](backend-java-spring-boot/README.md)
  - [Flask manual deployment notes](backend-flask-pytorch/README.md)

## Screenshots


![mask_rcnn_cats_and_dogs](https://github.com/user-attachments/assets/b6710505-8026-44fc-a5d3-c06e1a7e3abf)

<br />

![traffic_new_2](https://github.com/user-attachments/assets/256b72a9-111c-4f4a-bd90-de72ac2dc843)

<br />

![Neural Network Loading Spinner](https://github.com/user-attachments/assets/9ed0a3e3-00f5-4a86-a052-55ee9119377b)

<br />

# Stack/Technologies
  - Java Spring Boot
  - AWS ECS on EC2 Spot
  - AWS CDK
  - GitHub Actions
  - Docker and Nginx
  - TypeScript
  - Flask
  - Pytorch (Python)
  - AWS SageMaker/ Lambda (Heroku Version)

# PyTorch-Image-Classification-Project
- Personal project involving a Java Spring Boot API, Flask microservice, and TypeScript front end.
- The Java API sends requests to a Flask service hosting a PyTorch fasterrcnn_resnet50_fpn_v2 computer vision model.  This is deployed on an EC2 instance with its own Route 53 domain.
- This was originally deployed on Heroku as a TypeScript/Express.js application, using Amazon API Gateway to expose a lambda to send requests to a SageMaker endpoint.  I have refactored the project as this endpoint was costing roughly $50 a month.
- Can accept both an image URL or an uploaded image from one's computer.  It sends binary data to the lambda/ PyTorch Model either way.



# Deprecated Back End Repo - AWS SageMaker Endpoint/Model/etc
  - https://github.com/Mike11199/PyTorch-Image-Classification/

# Video - Old (2023)
  - https://www.youtube.com/watch?v=abtdBPFu_yM


# EC2 Screenshots
![image](https://github.com/user-attachments/assets/a4b823e0-6bf8-4e37-b228-bfc1980449aa)
![image](https://github.com/user-attachments/assets/829c1688-adbc-4587-b18a-dc9c7c073d44)

# Old Website Screenshots

![mask_rcnn_front_page](https://github.com/user-attachments/assets/94f6d43a-4b39-40b6-9887-7660cfc0cb3b)

<br />

![mask_rcnn_traffic](https://github.com/user-attachments/assets/b102cd8a-0103-4964-bf78-c34589f510db)

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

