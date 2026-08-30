# Notes

## Build Java Spring Boot Project with Maven
- mvn clean package
- outputs .jar to the "target" folder

## Run Java File Locally
- run locally `java -jar target/demo-0.0.1-SNAPSHOT.jar`

## Config
Add `application.properties` to `/src/main/resources` and then manually add these lines:
  - spring.servlet.multipart.max-file-size=100MB
  - spring.servlet.multipart.max-request-size=100MB

## Legacy EC2 / Nginx Notes (DEAD CODE)
These instructions were for building Maven jars on EC2 and running Java directly. They are no longer used — Docker containers now run the app, and CDK manages infrastructure. See [cdk/README.md](../cdk/README.md) for current deployment info.

- Note to self: Maven refused to build on EC2 `t2.micro`. Had to temporarily stop instance and scale up to `t2.large` for it to build. CI now runs in GitHub Actions, which might hit this same issue on small runners.
- Build with `mvn clean install`
- Skip tests with `mvn clean install -DskipTests`
- Runs in background: `nohup java -jar target/demo-0.0.1-SNAPSHOT.jar > output.log 2>&1 &`
- Check if app is running: `ps -ef | grep java`
- Remember to kill process before rebuilding if already running
- Add `application.properties` to `/src/main/resources`:
  - spring.servlet.multipart.max-file-size=100MB
  - spring.servlet.multipart.max-request-size=100MB
- Nginx commands (now inside container):
  - `sudo systemctl start nginx`
  - `sudo systemctl status nginx`
  - `sudo systemctl restart nginx`
