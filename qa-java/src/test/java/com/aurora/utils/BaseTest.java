package com.aurora.utils;

import com.aventstack.extentreports.ExtentReports;
import com.aventstack.extentreports.ExtentTest;
import com.aventstack.extentreports.reporter.ExtentSparkReporter;
import io.github.bonigarcia.wdm.WebDriverManager;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.TakesScreenshot;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.remote.RemoteWebDriver;
import org.testng.ITestResult;
import org.testng.annotations.*;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * Base class for all Aurora UI tests.
 * Manages: WebDriver lifecycle, ExtentReports setup, screenshots on failure.
 */
public class BaseTest {

    protected WebDriver driver;
    protected static ExtentReports extent;
    protected ExtentTest test;

    @BeforeSuite(alwaysRun = true)
    public static void initReports() {
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));
        String reportPath = "target/reports/aurora-report-" + timestamp + ".html";
        new File("target/reports").mkdirs();

        ExtentSparkReporter spark = new ExtentSparkReporter(reportPath);
        spark.config().setDocumentTitle("Aurora QA Report");
        spark.config().setReportName("Aurora Automated Test Results");
        spark.config().setTheme(com.aventstack.extentreports.reporter.configuration.Theme.DARK);

        extent = new ExtentReports();
        extent.attachReporter(spark);
        extent.setSystemInfo("Application", "Aurora AI Assistant");
        extent.setSystemInfo("URL", "http://localhost:5173");
        extent.setSystemInfo("Browser", "Chrome (headless)");
        extent.setSystemInfo("OS", System.getProperty("os.name"));
    }

    @BeforeMethod(alwaysRun = true)
    public void initDriver() throws Exception {
        WebDriverManager.chromedriver().setup();
        ChromeOptions options = new ChromeOptions();
        options.addArguments(
            "--headless=new",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--window-size=1920,1080",
            "--disable-gpu"
        );
        String remoteUrl = System.getenv("SELENIUM_REMOTE_URL");
        driver = remoteUrl == null || remoteUrl.isBlank()
            ? new ChromeDriver(options)
            : new RemoteWebDriver(java.net.URI.create(remoteUrl).toURL(), options);
        driver.manage().window().maximize();
    }

    @AfterMethod(alwaysRun = true)
    public void tearDownTest(ITestResult result) {
        if (result.getStatus() == ITestResult.FAILURE) {
            test.fail("Test failed: " + result.getThrowable().getMessage());
            captureScreenshot(result.getName());
        } else if (result.getStatus() == ITestResult.SUCCESS) {
            test.pass("Test passed");
        } else {
            test.skip("Test skipped: " + result.getSkipCausedBy());
        }

        if (driver != null) {
            driver.quit();
            driver = null;
        }
    }

    @AfterSuite(alwaysRun = true)
    public static void flushReports() {
        if (extent != null) {
            extent.flush();
            System.out.println("Extent report generated in target/reports/");
        }
    }

    private void captureScreenshot(String testName) {
        try {
            byte[] screenshot = ((TakesScreenshot) driver).getScreenshotAs(OutputType.BYTES);
            String screenshotPath = "target/screenshots/" + testName + "_" +
                LocalDateTime.now().format(DateTimeFormatter.ofPattern("HHmmss")) + ".png";
            new File("target/screenshots").mkdirs();
            Files.write(Paths.get(screenshotPath), screenshot);
            test.addScreenCaptureFromPath("../" + screenshotPath, "Failure Screenshot");
        } catch (Exception e) {
            test.warning("Could not capture screenshot: " + e.getMessage());
        }
    }
}
