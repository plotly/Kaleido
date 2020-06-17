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
#include "base/json/json_writer.h"
#include "base/strings/stringprintf.h"
#include "headless/public/devtools/domains/page.h"
#include "headless/public/devtools/domains/runtime.h"
#include "headless/public/headless_browser.h"
#include "headless/public/headless_devtools_client.h"
#include "headless/public/headless_devtools_target.h"
#include "headless/public/headless_web_contents.h"
#include "ui/gfx/geometry/size.h"

#include "headless/app/orca_next.h"
#include "plugins/Factory.h"
#include "plugins/BasePlugin.h"

#include <streambuf>
#include <fstream>
#include <iostream>
#include <utility>


#if defined(OS_WIN)
#include "content/public/app/sandbox_helper_win.h"
#include "sandbox/win/src/sandbox_types.h"
#endif

OrcaNext::OrcaNext(
        headless::HeadlessBrowser* browser,
        headless::HeadlessWebContents* web_contents,
        std::string tmpFileName,
        BasePlugin *plugin_ptr
)
        : tmpFileName(tmpFileName),
          remainingLocalScriptsFiles(plugin_ptr->LocalScriptFiles()),
          plugin(plugin_ptr),
          browser_(browser),
          web_contents_(web_contents),
          devtools_client_(headless::HeadlessDevToolsClient::Create()) {
    web_contents_->AddObserver(this);
}

OrcaNext::~OrcaNext() {
    // Note that we shut down the browser last, because it owns objects such as
    // the web contents which can no longer be accessed after the browser is gone.
    devtools_client_->GetPage()->RemoveObserver(this);
    web_contents_->GetDevToolsTarget()->DetachClient(devtools_client_.get());
    web_contents_->RemoveObserver(this);
    std::cerr << "Shutdown" << std::endl;
    browser_->Shutdown();
}

// This method is called when the tab is ready for DevTools inspection.
void OrcaNext::DevToolsTargetReady() {
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

void OrcaNext::OnLoadEventFired(
        const headless::page::LoadEventFiredParams& params) {
    // Enable runtime
    LoadNextScript();

    // Delete tmp file
    std::remove(tmpFileName.c_str());
}

void OrcaNext::OnExecutionContextCreated(
        const headless::runtime::ExecutionContextCreatedParams& params) {
    contextId = params.GetContext()->GetId();
}

void OrcaNext::LoadNextScript() {
     if (remainingLocalScriptsFiles.empty()) {
         // Finished processing startup scripts, start exporting figures
         ExportNextFigure();
     } else {
         // Load Script
         std::string scriptPath(remainingLocalScriptsFiles.front());
         remainingLocalScriptsFiles.pop_front();
         std::ifstream t(scriptPath);
         std::string scriptString((std::istreambuf_iterator<char>(t)),
                                  std::istreambuf_iterator<char>());

         devtools_client_->GetRuntime()->CompileScript(
                 scriptString,
                 scriptPath,
                 true,
                 base::BindOnce(&OrcaNext::OnScriptCompileComplete, weak_factory_.GetWeakPtr()));
     }
}

void OrcaNext::ExportNextFigure() {
    std::string exportSpec;

    // TODO: Test whether this will work for really large figures. Do we need to read chunks at some point?
    std::cerr << "Blocking for next figure" << std::endl;
    if (!std::getline(std::cin, exportSpec)) {
        std::cerr << "No more figures" << std::endl;
        // Reached end of file,
        // Shut down the browser (see ~OrcaNext).
        delete g_example;
        g_example = nullptr;

        return;
    }

    std::cerr << "Received Figure: " << std::endl;
    std::string exportFunction = base::StringPrintf(
            "function(spec, ...args) { return orca_next_plugins.%s(spec, ...args).then(JSON.stringify); }",
            plugin->PluginName().c_str());

    base::Optional<base::Value> json = base::JSONReader::Read(exportSpec);
    if (!json.has_value()) {
        std::cerr << "Invalid JSON: " << exportSpec << std::endl;
        ExportNextFigure();
        return;
    }

    std::vector<std::unique_ptr<::headless::runtime::CallArgument>> args = plugin->BuildCallArguments();

    // Prepend Export spec as first argument
    args.insert(args.begin(),
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
            base::BindOnce(&OrcaNext::OnExportComplete, weak_factory_.GetWeakPtr()));
}

void OrcaNext::OnExportComplete(
        std::unique_ptr<headless::runtime::CallFunctionOnResult> result) {
    std::cerr << "OnExportComplete" << "\n";
    // Make sure the evaluation succeeded before reading the result.
    if (result->HasExceptionDetails()) {
        LOG(ERROR) << "Failed to serialize document: "
                   << result->GetExceptionDetails()->GetText();
        ExportNextFigure();
    } else {
        // JSON parse result to get format
        std::string responseString = result->GetResult()->GetValue()->GetString();
        base::Optional<base::Value> responseJson = base::JSONReader::Read(responseString);
        const base::DictionaryValue* responseDict;
        responseJson.value().GetAsDictionary(&responseDict);

        // format
        std::string format;
        responseDict->GetString("format", &format);

        if (format == "pdf" || format == "eps") {
            std::string bgColor, imgData;
            responseDict->GetString("pdfBgColor", &bgColor);
            responseDict->GetString("result", &imgData);

            int width, height;
            responseDict->GetInteger("width", &width);
            responseDict->GetInteger("height", &height);

            double scale;
            responseDict->GetDouble("scale", &scale);

            std::cerr << "format: " << format << ", pdfBgColor:" << bgColor <<
                         ", width: " << width << ", height: " << height << ", scale: " << scale << std::endl;

            devtools_client_->GetPage()->GetExperimental()->PrintToPDF(
                    headless::page::PrintToPDFParams::Builder()
                            .SetMarginBottom(0)
                            .SetMarginTop(0)
                            .SetMarginLeft(0)
                            .SetMarginRight(0)
                            .SetPrintBackground(true)
                            .SetPreferCSSPageSize(true)  // Use @page {size: } CSS style
                            .Build(),
                    base::BindOnce(&OrcaNext::OnPDFCreated, weak_factory_.GetWeakPtr(), responseString));
        } else {
            std::cout << result->GetResult()->GetValue()->GetString().c_str() << std::endl;
            ExportNextFigure();
        }
    }
}

void OrcaNext::OnPDFCreated(
        std::string responseString,
        std::unique_ptr<headless::page::PrintToPDFResult> result
    ) {
  if (!result) {
    LOG(ERROR) << "Export to PDF failed";
    // TODO: write error as JSON
    return;
  } else {
      base::Optional<base::Value> responseJson = base::JSONReader::Read(responseString);
      base::DictionaryValue* responseDict;
      responseJson.value().GetAsDictionary(&responseDict);
      responseDict->SetString("result", result->GetData().toBase64());

      std::string response;
      base::JSONWriter::Write(*responseDict, &response);
      std::cout << response << "\n";
  }

  ExportNextFigure();
}

void OrcaNext::OnScriptCompileComplete(
        std::unique_ptr<headless::runtime::CompileScriptResult> result) {
    // Make sure the evaluation succeeded before running script
    if (result->HasExceptionDetails()) {
        LOG(ERROR) << "Failed to compile script: "
                   << result->GetExceptionDetails()->GetText();
    } else {
        std::string plotlyjsScriptId = result->GetScriptId();
        devtools_client_->GetRuntime()->RunScript(
                plotlyjsScriptId,
                base::BindOnce(&OrcaNext::OnRunScriptComplete, weak_factory_.GetWeakPtr())
                );
    }
}

void OrcaNext::OnRunScriptComplete(
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
    if (args.empty()) {
        LOG(ERROR) << "No Plugin Specified";
        browser->Shutdown();
        exit(EXIT_FAILURE);
        return;
    }

    // Instantiate renderer plugin
    std::string plugin_name = args[0];
    BasePlugin *plugin = LoadPlugin(plugin_name);
    if (!plugin) {
        // Invalid plugin name
        LOG(ERROR) << "Invalid plugin: " << plugin_name;
        browser->Shutdown();
        exit(EXIT_FAILURE);
        return;
    }

    // Build initial HTML file
    std::list<std::string> scriptTags = plugin->ScriptTags();
    std::stringstream htmlStringStream;
    htmlStringStream << "<html><head><meta charset=\"UTF-8\"><style id=\"head-style\"></style>";

    // Add script tags
    while (!scriptTags.empty()) {
        std::string tagValue = scriptTags.front();
        GURL tagUrl(tagValue);
        if (tagUrl.is_valid()) {
            // Value is a url, use a src of script tag
            htmlStringStream << "<script type=\"text/javascript\" src=\"" << tagValue << "\"></script>";
        } else {
            // Value is not a url, use a inline JavaScript code
            htmlStringStream << "<script>" << tagValue << "</script>\n";
        }
        scriptTags.pop_front();
    }
    // Close head and add body with img tag place holder for PDF export
    htmlStringStream << "</head><body style=\"{margin: 0; padding: 0;}\"><img id=\"orca-image\"><img></body></html>";

    // Write html to temp file
    std::string tmpFileName = std::tmpnam(nullptr) + std::string(".html");
    std::cerr << "Temp file: " << tmpFileName << std::endl;
    std::ofstream htmlFile;
    htmlFile.open(tmpFileName, std::ios::out);
    htmlFile << htmlStringStream.str();
    htmlFile.close();

    // Create file:// url to temp file
    GURL url = GURL(std::string("file://") + tmpFileName);

    // Open a tab (i.e., HeadlessWebContents) in the newly created browser context.
    headless::HeadlessWebContents::Builder tab_builder(
            browser_context->CreateWebContentsBuilder());

    // We could set other options for the opened tab here, for now only set URL
    tab_builder.SetInitialURL(url);

    // Create an instance of OrcaNext
    headless::HeadlessWebContents *web_contents = tab_builder.Build();

    // TODO make plugin a unique ptr and use move semantics here
    g_example = new OrcaNext(browser, web_contents, tmpFileName, plugin);
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
