#include "base/memory/weak_ptr.h"
#include "headless/public/devtools/domains/page.h"
#include "headless/public/devtools/domains/runtime.h"
#include "headless/public/headless_browser.h"
#include "headless/public/headless_devtools_client.h"
#include "headless/public/headless_devtools_target.h"
#include "headless/public/headless_web_contents.h"

#include "plugins/BasePlugin.h"

#ifndef CHROMIUM_ORCA_NEXT_H
#define CHROMIUM_ORCA_NEXT_H

// This class contains the main application logic, i.e., waiting for a page to
// load and printing its DOM. Note that browser initialization happens outside
// this class.
class OrcaNext : public headless::HeadlessWebContents::Observer,
                 public headless::page::Observer,
                 public headless::runtime::Observer
{
public:
    OrcaNext(headless::HeadlessBrowser* browser,
             headless::HeadlessWebContents* web_contents,
             std::string tmpFileName,
             BasePlugin *plugin);

    ~OrcaNext() override;

    // headless::HeadlessWebContents::Observer implementation:
    void DevToolsTargetReady() override;

    // headless::page::Observer implementation:
    void OnLoadEventFired(
            const headless::page::LoadEventFiredParams& params) override;

    void OnExecutionContextCreated(const headless::runtime::ExecutionContextCreatedParams& params) override;

    void ExportNextFigure();
    void LoadNextScript();
    void OnPDFCreated(std::string responseString, std::unique_ptr<headless::page::PrintToPDFResult> result);

    // Tip: Observe headless::inspector::ExperimentalObserver::OnTargetCrashed to
    // be notified of renderer crashes.
    void OnExportComplete(std::unique_ptr<headless::runtime::CallFunctionOnResult> result);
    void OnScriptCompileComplete(std::unique_ptr<headless::runtime::CompileScriptResult> result);
    void OnRunScriptComplete(std::unique_ptr<headless::runtime::RunScriptResult> result);

private:
    int contextId;
    std::string tmpFileName;
    std::list<std::string> remainingLocalScriptsFiles;
    BasePlugin *plugin;

    // The headless browser instance. Owned by the headless library. See main().
    headless::HeadlessBrowser* browser_;
    // Our tab. Owned by |browser_|.
    headless::HeadlessWebContents* web_contents_;
    // The DevTools client used to control the tab.
    std::unique_ptr<headless::HeadlessDevToolsClient> devtools_client_;
    // A helper for creating weak pointers to this class.
    // weak_factory_ MUST BE LAST PROPERTY DEFINED!
    base::WeakPtrFactory<OrcaNext> weak_factory_{this};
};

namespace {
    OrcaNext* g_example;
}

#endif //CHROMIUM_ORCA_NEXT_H
