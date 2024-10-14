# Notes

## Build Java Spring Boot Project with Maven
- mvn clean package
- outputs .jar to the "target" folder

## Run Java File
- java -jar target/demo-0.0.1-SNAPSHOT.jar

## Run Java EC2
- Runs in background with &, redirects stdout to output.log and stderr.  `nohup java -jar target/demo-0.0.1-SNAPSHOT.jar > output.log 2>&1 &`
- check if app is running `ps -ef | grep java`

## Start nginx - Frontend
- `sudo systemctl start nginx`