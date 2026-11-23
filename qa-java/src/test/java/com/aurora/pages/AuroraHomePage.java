package com.aurora.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;
import java.util.List;

/**
 * Page Object Model for Aurora's main UI.
 * Encapsulates all element locators and interactions.
 * Never contains assertions — that belongs in test classes.
 */
public class AuroraHomePage {

    private final WebDriver driver;
    private final WebDriverWait wait;
    public static final String BASE_URL = System.getenv().getOrDefault("AURORA_URL", "http://localhost:5173");

    // Locators
    private static final By HEADER_TITLE      = By.tagName("h1");
    private static final By DARK_MODE_TOGGLE  = By.cssSelector("button[aria-label*='dark'], button[title*='dark']");
    private static final By AI_ORB            = By.cssSelector("[data-testid='ai-orb'], .cursor-pointer");
    private static final By CHAT_INPUT        = By.cssSelector("input[placeholder*='message'], textarea");
    private static final By SEND_BUTTON       = By.cssSelector("button[type='submit']");
    private static final By MESSAGE_LIST      = By.cssSelector("[data-testid='message'], .message-bubble");
    private static final By CONNECTION_DOT    = By.cssSelector("[data-testid='connection-status']");
    private static final By MODEL_SELECTOR    = By.cssSelector("[data-testid='model-select'], select");
    private static final By AGENT_NAVIGATION = By.xpath("//nav//button[.//span[normalize-space()='Agent']]");
    private static final By AGENT_HEADING = By.xpath("//h1[normalize-space()='Agent tasks']");

    public AuroraHomePage(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(15));
    }

    // ── Navigation ──────────────────────────────────────────────────────────

    public void navigate() {
        driver.get(BASE_URL);
    }

    // ── Getters ─────────────────────────────────────────────────────────────

    public String getHeaderTitle() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(HEADER_TITLE)).getText();
    }

    public String getPageTitle() {
        return driver.getTitle();
    }

    public List<WebElement> getMessages() {
        return driver.findElements(MESSAGE_LIST);
    }

    public int getMessageCount() {
        return getMessages().size();
    }

    // ── State checks ────────────────────────────────────────────────────────

    public boolean isChatInputVisible() {
        try {
            return driver.findElement(CHAT_INPUT).isDisplayed();
        } catch (Exception e) { return false; }
    }

    public boolean isConnectionDotVisible() {
        try {
            return driver.findElement(CONNECTION_DOT).isDisplayed();
        } catch (Exception e) { return false; }
    }

    // ── Actions ─────────────────────────────────────────────────────────────

    public void sendMessage(String text) {
        WebElement input = wait.until(ExpectedConditions.elementToBeClickable(CHAT_INPUT));
        input.clear();
        input.sendKeys(text);
        driver.findElement(SEND_BUTTON).click();
    }

    public void clickAiOrb() {
        wait.until(ExpectedConditions.elementToBeClickable(AI_ORB)).click();
    }

    public void openAgentTasks() {
        wait.until(ExpectedConditions.elementToBeClickable(AGENT_NAVIGATION)).click();
    }

    public String getAgentHeading() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(AGENT_HEADING)).getText();
    }

    public void waitForMessageCount(int expectedCount) {
        wait.until(d -> getMessageCount() >= expectedCount);
    }
}
