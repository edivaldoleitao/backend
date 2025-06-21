import time
from playwright.sync_api import sync_playwright

class Scraper:

    def init_browser(self):
      """Inicializa o navegador com Playwright."""
      playwright = sync_playwright().start()
      browser = playwright.chromium.launch(headless=False)
      page = browser.new_page()
      return playwright, browser, page

    def element_visible(self, locator):
      result = False
      try:
        for i in range(locator.count()):
          if locator.nth(i).is_visible():
            result = True
            break
      except:
        pass
      return result

    def any_elements_visible(self, locators=[]):
      result = False
      try:
        for i in range(len(locators)):
          try:
            for j in range(locators[i].count()):
              if locators[i].nth(j).is_visible():
                  result = True
          except:
            pass
          if result:
            break
      except:
        pass
      return result

    def wait_element_and_click(self, page, locator, timeout=10000, timeout_before=100, force=False, no_wait_after=False):
      page.wait_for_timeout(timeout_before)
      if self.wait_element(locator, timeout=timeout):
        locator.click(force=force, no_wait_after=no_wait_after)
        return True
      else:
        return False

    def wait_element(self, locator, timeout=10000, visible=True):
      find_result = False

      current_timeout = 0
      while(current_timeout <= timeout and not find_result):
        try:
          if visible:
            locator.first.wait_for(state="visible", timeout=500)
            find_result = True
          else:
            time.sleep(0.5)
            if locator.count() > 0:
              find_result = True
            else:
              current_timeout = current_timeout + 500
        except:
          current_timeout = current_timeout + 500

      return find_result

    def wait_elements(self, page, locators, timeout=20000, return_locator=False, visible=True):
      time_count  = 0
      find_result = False
      locator     = None
      while not find_result and time_count < timeout:
        for i in range(len(locators)):
          try:
            for j in range(locators[i].count()):
              if visible:
                if locators[i].nth(j).is_visible():
                  find_result = True
                  locator = locators[i].nth(j)
                break
              elif locators[i].nth(j).count() > 0:
                find_result = True
                locator = locators[i].nth(j)
                break
          except:
            pass
          time_count = time_count + 500
          try:
            page.wait_for_timeout(500)
          except:
            time.sleep(0.5)

      if return_locator:
        return locator
      else:
        return find_result

    def wait_element_disappear(self, page, locator, timeout=60000, timeout_page=1000):
      try:
        page.wait_for_timeout(timeout_page)
      except:
        time.sleep(0.1)

      current_timeout = 0
      while(current_timeout <= timeout):
        try:
          if locator.count() == 1:
            locator.wait_for(state="hidden", timeout=500)
          elif locator.count() > 1:
            for i in range(locator.count()):
              locator.nth(i).wait_for(state="hidden", timeout=500)
              break
        except:
          current_timeout = current_timeout + 500
