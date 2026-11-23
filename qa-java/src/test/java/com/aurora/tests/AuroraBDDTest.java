package com.aurora.tests;

import io.cucumber.testng.AbstractTestNGCucumberTests;
import io.cucumber.testng.CucumberOptions;

@CucumberOptions(
    features = "src/test/resources/features",
    glue = "com.aurora.steps",
    plugin = {"pretty", "html:target/cucumber-report.html", "junit:target/cucumber-results.xml"}
)
public class AuroraBDDTest extends AbstractTestNGCucumberTests {
}
