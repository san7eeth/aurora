package com.aurora.tests;

import io.restassured.RestAssured;
import io.restassured.response.Response;
import org.testng.Assert;
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
        RestAssured.baseURI = "http://localhost:8000";
        RestAssured.enableLoggingOfRequestAndResponseIfValidationFails();
    }

    @Test(description = "GET /health returns 200 with status=ok")
    public void testHealthReturnsOk() {
        given()
            .when()
                .get("/health")
            .then()
                .statusCode(200)
                .body("status", equalTo("ok"))
                .body("version", notNullValue())
                .body("model", notNullValue())
                .body("ollama", notNullValue());
    }

    @Test(description = "GET /api/models returns models list and active model")
    public void testModelsEndpointReturnsData() {
        given()
            .when()
                .get("/api/models")
            .then()
                .statusCode(200)
                .body("models", notNullValue())
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

    @Test(description = "POST /api/models/select with valid model returns 200")
    public void testSelectModelValidReturns200() {
        Response response = given()
            .contentType("application/json")
            .body("{\"model\": \"phi3:mini\"}")
            .when()
                .post("/api/models/select")
            .then()
                .statusCode(200)
                .extract().response();

        String active = response.jsonPath().getString("active");
        Assert.assertEquals(active, "phi3:mini", "Active model should be updated");
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
