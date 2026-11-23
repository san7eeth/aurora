package com.aurora.steps;

import io.cucumber.java.en.And;
import io.cucumber.java.en.Given;
import io.cucumber.java.en.Then;
import io.cucumber.java.en.When;
import io.restassured.response.Response;

import static io.restassured.RestAssured.given;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.anyOf;

public class HealthSteps {
    private String baseUrl;
    private Response response;

    @Given("the Aurora API is configured")
    public void configureApi() {
        baseUrl = System.getenv().getOrDefault("BACKEND_URL", "http://localhost:8000");
    }

    @When("I request the health endpoint")
    public void requestHealth() {
        response = given().get(baseUrl + "/health");
    }

    @Then("the health endpoint responds successfully")
    public void healthResponds() {
        assertThat(response.statusCode(), equalTo(200));
        assertThat(response.jsonPath().getString("status"), anyOf(equalTo("ok"), equalTo("degraded")));
    }

    @And("the database reports ready")
    public void databaseReady() {
        assertThat(response.jsonPath().getString("database"), equalTo("ok"));
    }
}
