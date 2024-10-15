# Notes

## Build Java Spring Boot Project with Maven
- mvn clean package
- outputs .jar to the "target" folder

## Run Java File
- run locally `java -jar target/demo-0.0.1-SNAPSHOT.jar`

## Run Java EC2
- Note to self - Maven refuses to build on EC2 `t2.micro`.  Had to temporarily stop instance and scale up to `t2.large` for it to build.  So a CI/CD pipeline from Github might not work due to this.
- Runs in background with &, redirects stdout to output.log and stderr.  `nohup java -jar target/demo-0.0.1-SNAPSHOT.jar > output.log 2>&1 &`
- check if app is running `ps -ef | grep java`
- build with `mvn clean install`
- skip tests with `mvn clean install -DskipTests`
- remember to kill process if running to build again
- Add `application.properties` to `/home/ec2-user/pytorch-projects/PyTorch-Image-Classification-TypeScript/backend-java-spring-boot/src/main/resources` and then manually add these lines:
  - spring.servlet.multipart.max-file-size=100MB
  - spring.servlet.multipart.max-request-size=100MB

## Start nginx - Frontend
- `sudo systemctl start nginx`
- `sudo systemctl status nginx`
- `sudo systemctl restart nginx`
