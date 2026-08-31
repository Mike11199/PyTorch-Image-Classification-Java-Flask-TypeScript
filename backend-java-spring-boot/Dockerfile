# Java Spring Boot backend - multi-stage: Maven build → run JAR
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /app
COPY backend-java-spring-boot/pom.xml .
RUN mvn dependency:go-offline -B || true
COPY backend-java-spring-boot/. .
RUN mvn clean package -DskipTests

# Run the built JAR with minimal image
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app

# Runtime configuration under src/main/resources is packaged inside the JAR.
COPY --from=build /app/target/demo-0.0.1-SNAPSHOT.jar app.jar
RUN addgroup -g 1001 spring && \
    adduser -u 1001 -G spring -s /bin/sh -D spring && \
    chown -R spring:spring /app

USER spring:spring

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
