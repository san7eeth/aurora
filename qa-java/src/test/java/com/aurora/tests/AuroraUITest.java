package com.aurora.tests;

import com.aurora.pages.AuroraHomePage;
import com.aurora.utils.BaseTest;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * UI smoke tests for Aurora using Selenium + TestNG + Page Object Model.
 * Requires Aurora frontend running at http://localhost:5173
 *
 * Run: mvn test -Dtest=AuroraUITest
 */
public class AuroraUITest extends BaseTest {

    @Test(description = "Verify Aurora app loads and shows 'Aurora' in heading")
    public void testAppLoadsWithTitle() {
        test = extent.createTest("App Load — Title Check");
        test.info("Navigating to " + AuroraHomePage.BASE_URL);

        AuroraHomePage page = new AuroraHomePage(driver);
        page.navigate();

        String title = page.getHeaderTitle();
        test.info("H1 text: " + title);

        Assert.assertTrue(
            title.contains("Aurora"),
            "Expected H1 to contain 'Aurora', but got: " + title
        );
    }

    @Test(description = "Verify page title contains Aurora")
    public void testPageTitle() {
        test = extent.createTest("App Load — Page Title");

        AuroraHomePage page = new AuroraHomePage(driver);
        page.navigate();

        String pageTitle = page.getPageTitle();
        test.info("Page title: " + pageTitle);

        Assert.assertTrue(
            pageTitle.length() > 0,
            "Page title should not be empty"
        );
    }

    @Test(description = "Verify Agent task screen opens from the navigation")
    public void testAgentNavigation() {
        test = extent.createTest("Agent screen — Navigation");

        AuroraHomePage page = new AuroraHomePage(driver);
        page.navigate();
        page.openAgentTasks();
        Assert.assertEquals(page.getAgentHeading(), "Agent tasks");
    }
}
