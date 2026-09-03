# Stage 1: compile the class file with the full JDK
FROM eclipse-temurin:21-jdk-alpine AS build
WORKDIR /src
COPY HelloWorld.java ./
RUN javac HelloWorld.java

# Stage 2: run it on the smaller JRE image, without the compiler
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=build /src/HelloWorld.class ./

EXPOSE 8080
CMD ["java", "HelloWorld"]
