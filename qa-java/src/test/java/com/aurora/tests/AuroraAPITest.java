package com.aurora.tests;

import io.restassured.RestAssured;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

/**
 * Aurora Backend API tests using REST Assured.
 * Requires Aurora backend running at http://localhost:8000
 *
 * Run: mvn test -Dtest=AuroraAPITest
 */
public class AuroraAPITest {

    @BeforeClass
    public void setup() {
        RestAssured.baseURI = System.getenv().getOrDefault("BACKEND_URL", "http://localhost:8000");
        RestAssured.enableLoggingOfRequestAndResponseIfValidationFails();
    }

    @Test(description = "GET /health returns a live health state")
    public void testHealthReturnsOk() {
        given()
            .when()
                .get("/health")
            .then()
                .statusCode(200)
                .body("status", anyOf(equalTo("ok"), equalTo("degraded")))
                .body("database", equalTo("ok"))
                .body("version", notNullValue())
                .body("model", notNullValue())
                .body("ollama", notNullValue());
    }

    @Test(description = "GET /api/models/active returns the configured model")
    public void testActiveModelEndpointReturnsData() {
        given()
            .when()
                .get("/api/models/active")
            .then()
                .statusCode(200)
                .body("active", notNullValue());
    }

    @Test(description = "POST /api/models/select with empty name returns 400")
    public void testSelectModelEmptyReturns400() {
        given()
            .contentType("application/json")
            .body("{\"model\": \"\"}")
            .when()
                .post("/api/models/select")
            .then()
                .statusCode(400)
                .body("error", notNullValue());
    }

    @Test(description = "Health response time is under 5 seconds")
    public void testHealthResponseTime() {
        given()
            .when()
                .get("/health")
            .then()
                .statusCode(200)
                .time(lessThan(5000L));
    }
}
