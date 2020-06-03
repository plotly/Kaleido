// Copyright 2017 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

// A small example application showing the use of the C++ Headless Chrome
// library. It navigates to a web site given on the command line, waits for it
// to load and prints out the DOM.
//
// Tip: start reading from the main() function below.

#include "base/bind.h"
#include "base/command_line.h"
#include "base/memory/weak_ptr.h"
#include "base/json/json_reader.h"
#include "headless/public/devtools/domains/page.h"
#include "headless/public/devtools/domains/runtime.h"
#include "headless/public/headless_browser.h"
#include "headless/public/headless_devtools_client.h"
#include "headless/public/headless_devtools_target.h"
#include "headless/public/headless_web_contents.h"
#include "ui/gfx/geometry/size.h"

#include <streambuf>
#include <fstream>
#include <iostream>
#include <utility>


#if defined(OS_WIN)
#include "content/public/app/sandbox_helper_win.h"
#include "sandbox/win/src/sandbox_types.h"
#endif

// This class contains the main application logic, i.e., waiting for a page to
// load and printing its DOM. Note that browser initialization happens outside
// this class.
class HeadlessExample : public headless::HeadlessWebContents::Observer,
                        public headless::page::Observer,
                        public headless::runtime::Observer
                        {
public:
    HeadlessExample(headless::HeadlessBrowser* browser,
                    headless::HeadlessWebContents* web_contents,
                    std::list<std::string> startupScripts);

    ~HeadlessExample() override;

    // headless::HeadlessWebContents::Observer implementation:
    void DevToolsTargetReady() override;

    // headless::page::Observer implementation:
    void OnLoadEventFired(
            const headless::page::LoadEventFiredParams& params) override;

    void OnExecutionContextCreated(const headless::runtime::ExecutionContextCreatedParams& params) override;

    void ExportNextFigure();
    void LoadNextScript();

    // Tip: Observe headless::inspector::ExperimentalObserver::OnTargetCrashed to
    // be notified of renderer crashes.
//    void OnExportComplete(std::unique_ptr<headless::runtime::EvaluateResult> result);
    void OnExportComplete(std::unique_ptr<headless::runtime::CallFunctionOnResult> result);
    void OnScriptCompileComplete(std::unique_ptr<headless::runtime::CompileScriptResult> result);
    void OnRunScriptComplete(std::unique_ptr<headless::runtime::RunScriptResult> result);
//    void OnRuntimeEnabled(std::unique_ptr<headless::runtime::EnableResult>);

private:
    int contextId;
    std::list<std::string> startupScripts;

    // The headless browser instance. Owned by the headless library. See main().
    headless::HeadlessBrowser* browser_;
    // Our tab. Owned by |browser_|.
    headless::HeadlessWebContents* web_contents_;
    // The DevTools client used to control the tab.
    std::unique_ptr<headless::HeadlessDevToolsClient> devtools_client_;
    // A helper for creating weak pointers to this class.
    // weak_factory_ MUST BE LAST PROPERTY DEFINED!
    base::WeakPtrFactory<HeadlessExample> weak_factory_{this};
};

namespace {
    HeadlessExample* g_example;
}

HeadlessExample::HeadlessExample(
        headless::HeadlessBrowser* browser,
        headless::HeadlessWebContents* web_contents,
        std::list<std::string> startupScripts
)
        : startupScripts(std::move(startupScripts)),
          browser_(browser),
          web_contents_(web_contents),
          devtools_client_(headless::HeadlessDevToolsClient::Create()) {
    web_contents_->AddObserver(this);
}

HeadlessExample::~HeadlessExample() {
    // Note that we shut down the browser last, because it owns objects such as
    // the web contents which can no longer be accessed after the browser is gone.
    devtools_client_->GetPage()->RemoveObserver(this);
    web_contents_->GetDevToolsTarget()->DetachClient(devtools_client_.get());
    web_contents_->RemoveObserver(this);
    browser_->Shutdown();
}

// This method is called when the tab is ready for DevTools inspection.
void HeadlessExample::DevToolsTargetReady() {
    // Attach our DevTools client to the tab so that we can send commands to it
    // and observe events.
    web_contents_->GetDevToolsTarget()->AttachClient(devtools_client_.get());

    // Start observing events from DevTools's page domain. This lets us get
    // notified when the page has finished loading. Note that it is possible
    // the page has already finished loading by now. See
    // HeadlessShell::DevToolTargetReady for how to handle that case correctly.
    devtools_client_->GetPage()->AddObserver(this);
    devtools_client_->GetPage()->Enable();

    devtools_client_->GetRuntime()->AddObserver(this);
    devtools_client_->GetRuntime()->Enable();
}

void HeadlessExample::OnLoadEventFired(
        const headless::page::LoadEventFiredParams& params) {
    // Enable runtime
    LoadNextScript();
}

void HeadlessExample::OnExecutionContextCreated(
        const headless::runtime::ExecutionContextCreatedParams& params) {
    contextId = params.GetContext()->GetId();
}

void HeadlessExample::LoadNextScript() {
     if (startupScripts.empty()) {
         // Finished processing startup scripts, start exporting figures
         ExportNextFigure();
     } else {
         // Load Plotly.js from local plotly.js bundle
         std::string scriptPath(startupScripts.front());
         startupScripts.pop_front();
         std::ifstream t(scriptPath);
         std::string scriptString((std::istreambuf_iterator<char>(t)),
                                  std::istreambuf_iterator<char>());

         devtools_client_->GetRuntime()->CompileScript(
                 scriptString,
                 scriptPath,
                 true,
                 base::BindOnce(&HeadlessExample::OnScriptCompileComplete, weak_factory_.GetWeakPtr()));
     }
}

void HeadlessExample::ExportNextFigure() {
    std::string exportSpec;

    // TODO: Test whether this will work for really large figures. Do we need to read chunks at some point?
    if (!std::getline(std::cin, exportSpec)) {
        // Reached end of file,
        // Shut down the browser (see ~HeadlessExample).
        delete g_example;
        g_example = nullptr;
        return;
    }

    std::string exportFunction = "function(spec) { return exportFromSpec(spec); }";

    base::Optional<base::Value> json = base::JSONReader::Read(exportSpec);
    if (!json.has_value()) {
        // TODO: write JSON repsonse to cout
        std::cerr << "Invalid JSON Export Request" << std::endl;
        ExportNextFigure();
        return;
    }

    std::vector<std::unique_ptr<::headless::runtime::CallArgument>> args;
    args.push_back(
            headless::runtime::CallArgument::Builder()
                    .SetValue(base::Value::ToUniquePtrValue(json->Clone()))
                    .Build()
    );

    std::unique_ptr<headless::runtime::CallFunctionOnParams> eval_params =
            headless::runtime::CallFunctionOnParams::Builder()
            .SetFunctionDeclaration(exportFunction)
            .SetArguments(std::move(args))
            .SetExecutionContextId(contextId)
            .SetAwaitPromise(true).Build();

    devtools_client_->GetRuntime()->CallFunctionOn(
            std::move(eval_params),
            base::BindOnce(&HeadlessExample::OnExportComplete, weak_factory_.GetWeakPtr()));

    // Create expression that evaluates to a promise. This figure should become the input figure
//    std::stringstream exprStringStream = std::stringstream();
//    exprStringStream << "(function(){"
//                     << "var spec = " << exportSpec << ";"
//                     <<  "return Plotly.toImage(spec.figure, {format: spec.format || 'png', scale: spec.scale || 1.0, width: spec.width || 700, height: spec.height || 450});"
//                     << "})()";
//
//    std::cerr << exprStringStream.str();
//    std::unique_ptr<headless::runtime::EvaluateParams> eval_params =
//            headless::runtime::EvaluateParams::Builder().SetExpression(
//                    exprStringStream.str()
//            ).SetAwaitPromise(true).Build();
//
//    std::cerr << "Evaluate... " << "\n";
//    devtools_client_->GetRuntime()->Evaluate(
//            std::move(eval_params),
//            base::BindOnce(&HeadlessExample::OnExportComplete, weak_factory_.GetWeakPtr()));
}

void HeadlessExample::OnExportComplete(
        std::unique_ptr<headless::runtime::CallFunctionOnResult> result) {
    std::cerr << "OnExportComplete" << "\n";
    // Make sure the evaluation succeeded before reading the result.
    if (result->HasExceptionDetails()) {
        LOG(ERROR) << "Failed to serialize document: "
                   << result->GetExceptionDetails()->GetText();
    } else {
        printf("%s\n", result->GetResult()->GetValue()->GetString().c_str());
    }
    // Repeat for next figure on standard-in
    ExportNextFigure();
}

//void HeadlessExample::OnExportComplete(
//        std::unique_ptr<headless::runtime::EvaluateResult> result) {
//    std::cerr << "OnExportComplete" << "\n";
//    // Make sure the evaluation succeeded before reading the result.
//    if (result->HasExceptionDetails()) {
//        LOG(ERROR) << "Failed to serialize document: "
//                   << result->GetExceptionDetails()->GetText();
//    } else {
//        printf("%s\n", result->GetResult()->GetValue()->GetString().c_str());
//    }
//    // Repeat for next figure on standard-in
//    ExportNextFigure();
//}

void HeadlessExample::OnScriptCompileComplete(
        std::unique_ptr<headless::runtime::CompileScriptResult> result) {
    // Make sure the evaluation succeeded before running script
    if (result->HasExceptionDetails()) {
        LOG(ERROR) << "Failed to compile script: "
                   << result->GetExceptionDetails()->GetText();
    } else {
        std::string plotlyjsScriptId = result->GetScriptId();
        devtools_client_->GetRuntime()->RunScript(
                plotlyjsScriptId,
                base::BindOnce(&HeadlessExample::OnRunScriptComplete, weak_factory_.GetWeakPtr())
                );
    }
}

void HeadlessExample::OnRunScriptComplete(
        std::unique_ptr<headless::runtime::RunScriptResult> result) {
    std::cerr << "OnRunScriptComplete" << "\n";
    // Make sure the evaluation succeeded before reading the result.
    if (result->HasExceptionDetails()) {
        LOG(ERROR) << "Failed to run script: "
                   << result->GetExceptionDetails()->GetText();
    } else {
        LoadNextScript();
    }
}

// This function is called by the headless library after the browser has been
// initialized. It runs on the UI thread.
void OnHeadlessBrowserStarted(headless::HeadlessBrowser* browser) {
    // In order to open tabs, we first need a browser context. It corresponds to a
    // user profile and contains things like the user's cookies, local storage,
    // cache, etc.
    headless::HeadlessBrowserContext::Builder context_builder =
            browser->CreateBrowserContextBuilder();

    // Here we can set options for the browser context. As an example we enable
    // incognito mode, which makes sure profile data is not written to disk.
    context_builder.SetIncognitoMode(true);

    // Construct the context and set it as the default. The default browser
    // context is used by the Target.createTarget() DevTools command when no other
    // context is given.
    headless::HeadlessBrowserContext* browser_context = context_builder.Build();
    browser->SetDefaultBrowserContext(browser_context);

    // Get the URL from the command line.
    base::CommandLine::StringVector args =
            base::CommandLine::ForCurrentProcess()->GetArgs();

    // Initialize vector of initialization JavaScript scripts
    std::list<std::string> scripts;

    bool localPlotlyjs = true;

    GURL url;
    if (localPlotlyjs) {
        // Empty HTML document, we will load plotly.js as a script after initialization
        scripts.emplace_back("/home/jmmease/scratch/plotly-latest.min.js");
        url = GURL(
                "data:text/html,<html></html>"
        );
    } else {
        // Load plotly.js from CDN
        url = GURL(
                "data:text/html,<html>"
                "<script type=\"text/javascript\" src=\"https://cdn.plot.ly/plotly-latest.min.js\"></script>"
                "</html>"
        );
    }

    // Additional initialization scripts (these must be added after plotly.js)
    scripts.emplace_back("./js/utils.js");

    // Open a tab (i.e., HeadlessWebContents) in the newly created browser
    // context.
    headless::HeadlessWebContents::Builder tab_builder(
            browser_context->CreateWebContentsBuilder());

    // We can set options for the opened tab here. In this example we are just
    // setting the initial URL to navigate to.
    tab_builder.SetInitialURL(url);

    // Create an instance of the example app, which will wait for the page to load
    // and print its DOM.
    headless::HeadlessWebContents *web_contents = tab_builder.Build();

    g_example = new HeadlessExample(browser, web_contents, scripts);
}

int main(int argc, const char** argv) {
#if !defined(OS_WIN)
    // This function must be the first thing we call to make sure child processes
    // such as the renderer are started properly. The headless library starts
    // child processes by forking and exec'ing the main application.
    headless::RunChildProcessIfNeeded(argc, argv);
#endif

    // Create a headless browser instance. There can be one of these per process
    // and it can only be initialized once.
    headless::HeadlessBrowser::Options::Builder builder(argc, argv);

#if defined(OS_WIN)
    // In windows, you must initialize and set the sandbox, or pass it along
  // if it has already been initialized.
  sandbox::SandboxInterfaceInfo sandbox_info = {0};
  content::InitializeSandboxInfo(&sandbox_info);
  builder.SetSandboxInfo(&sandbox_info);
#endif
    // Here you can customize browser options. As an example we set the window
    // size.
    builder.SetWindowSize(gfx::Size(800, 600));

    // Pass control to the headless library. It will bring up the browser and
    // invoke the given callback on the browser UI thread. Note: if you need to
    // pass more parameters to the callback, you can add them to the Bind() call
    // below.
    return headless::HeadlessBrowserMain(
            builder.Build(), base::BindOnce(&OnHeadlessBrowserStarted));
}
