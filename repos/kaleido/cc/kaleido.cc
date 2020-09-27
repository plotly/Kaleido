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
#include "base/strings/string_split.h"
#include "base/files/file_util.h"
#include "base/environment.h"
#include "headless/public/devtools/domains/page.h"
#include "headless/public/devtools/domains/runtime.h"
#include "headless/public/headless_browser.h"
#include "headless/public/headless_devtools_client.h"
#include "headless/public/headless_devtools_target.h"
#include "headless/public/headless_web_contents.h"
#include "ui/gfx/geometry/size.h"

#include "headless/app/kaleido.h"
#include "scopes/Factory.h"
#include "scopes/Base.h"
#include "utils.h"

#include <streambuf>
#include <fstream>
#include <iostream>
#include <utility>
#include "stdlib.h"


#if defined(OS_WIN)
#include "content/public/app/sandbox_helper_win.h"
#include "sandbox/win/src/sandbox_types.h"

namespace base {
    // Chromium doens't provide and implementation of ExecutableExistsInPath on Windows, so we add one here
    bool ExecutableExistsInPath(Environment* env,
        const std::string& executable) {
        std::string path;
        if (!env->GetVar("PATH", &path)) {
            LOG(ERROR) << "No $PATH variable. Assuming no " << executable << ".";
            return false;
        }

        for (const StringPiece& cur_path:
            SplitStringPiece(path, ";", KEEP_WHITESPACE, SPLIT_WANT_NONEMPTY)) {
            
            // Build wide strings using wstringstreams
            std::wstringstream wpath_ss;
            wpath_ss << cur_path.as_string().c_str();

            std::wstringstream wexecutable_ss;
            wexecutable_ss << executable.c_str() << ".exe";

            FilePath::StringPieceType w_cur_path(wpath_ss.str());
            FilePath file(w_cur_path);

            if (PathExists(file.Append(wexecutable_ss.str()))) {
                return true;
            }
        }
        return false;
    }
}
#endif

Kaleido::Kaleido(
        headless::HeadlessBrowser* browser,
        headless::HeadlessWebContents* web_contents,
        std::string tmpFileName,
        kaleido::scopes::BaseScope *scope_ptr
)
        : tmpFileName(tmpFileName),
          scope(scope_ptr),
          env(base::Environment::Create()),
          popplerAvailable(base::ExecutableExistsInPath(env.get(), "pdftops")),
          inkscapeAvailable(base::ExecutableExistsInPath(env.get(), "inkscape")),
          browser_(browser),
          web_contents_(web_contents),
          devtools_client_(headless::HeadlessDevToolsClient::Create()) {

    // Populate remainingLocalScriptsFiles vector
    for (std::string const &s: scope_ptr->LocalScriptFiles()) {
        localScriptFiles.push_back(s);
    }
    base::GetCurrentDirectory(&cwd);
    web_contents_->AddObserver(this);
}

Kaleido::~Kaleido() {

    // Delete tmp file
    std::remove(tmpFileName.c_str());

    // Note that we shut down the browser last, because it owns objects such as
    // the web contents which can no longer be accessed after the browser is gone.
    devtools_client_->GetPage()->RemoveObserver(this);
    web_contents_->GetDevToolsTarget()->DetachClient(devtools_client_.get());
    web_contents_->RemoveObserver(this);
    browser_->Shutdown();
}

// This method is called when the tab is ready for DevTools inspection.
void Kaleido::DevToolsTargetReady() {
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

void Kaleido::OnLoadEventFired(
        const headless::page::LoadEventFiredParams& params) {
    // Enable runtime
    nextScriptIndex = 0;
    LoadNextScript();
}

void Kaleido::OnExecutionContextCreated(
        const headless::runtime::ExecutionContextCreatedParams& params) {
    contextId = params.GetContext()->GetId();
}

void Kaleido::LoadNextScript() {
     if (localScriptFiles.size() <= nextScriptIndex) {
         // Finished processing startup scripts, get heap memory usage, which will then start ExportNext loop
         devtools_client_->GetRuntime()->Evaluate(
                 "JSON.stringify({jsHeapSizeLimit: window.performance.memory.jsHeapSizeLimit})",
                 base::BindOnce(&Kaleido::OnHeapEvalComplete, weak_factory_.GetWeakPtr()));
         return;
     } else {
         // Load Script
         std::string scriptPath(localScriptFiles[nextScriptIndex++]);
         std::ifstream t(scriptPath);
         if (!t.is_open()) {
             // Reached end of file,
             // Shut down the browser (see ~Kaleido).
             LOG(ERROR) << "Failed to find, or open, local file at "
                        << scriptPath << " with working directory " << cwd.value() << std::endl;
             delete g_example;
             g_example = nullptr;
             return;
         }
         std::string scriptString((std::istreambuf_iterator<char>(t)),
                                  std::istreambuf_iterator<char>());

         devtools_client_->GetRuntime()->CompileScript(
                 scriptString,
                 scriptPath,
                 true,
                 base::BindOnce(&Kaleido::OnScriptCompileComplete, weak_factory_.GetWeakPtr()));
     }
}

void Kaleido::ExportNext() {
    std::string exportSpec;
    while (true) {
        // Loop until we receive a valid export request, break loop below when a valid request is received
        if (!std::getline(std::cin, exportSpec)) {
            // Reached end of file,
            // Shut down the browser (see ~Kaleido).
            delete g_example;
            g_example = nullptr;
            return;
        }

        base::Optional<base::Value> json = base::JSONReader::Read(exportSpec);

        if (!json.has_value()) {
            kaleido::utils::writeJsonMessage(1, "Invalid JSON");
            continue;
        }

        // Read "operation" key, defaulting to "export" if none provided.
        std::string *maybe_operation = json->FindStringKey("operation");
        std::string operation;
        if (maybe_operation) {
            operation = *maybe_operation;
        } else {
            operation = std::string("export");
        }

        // Only operation right now is export, but others can be added in the future
        if (operation != "export") {
            // Unsupported operation
            kaleido::utils::writeJsonMessage(1, base::StringPrintf("Invalid operation: %s", operation.c_str()));
            continue;
        } else {
            std::string *maybe_format = json->FindStringKey("format");
            if (maybe_format) {
                std::string format = *maybe_format;

                // Validate poppler installed if format is eps
                if (format == "eps" && !popplerAvailable) {
                    kaleido::utils::writeJsonMessage(
                            530,
                            "Exporting to EPS format requires the pdftops command "
                            "which is provided by the poppler library. "
                            "Please install poppler and make sure the pdftops command "
                            "is available on the PATH");
                    continue;
                }

                // Validate inkscape installed if format is emf
                if (format == "emf" && !inkscapeAvailable) {
                    kaleido::utils::writeJsonMessage(
                            530,
                            "Exporting to EMF format requires inkscape. "
                            "Please install inkscape and make sure it is available on the PATH");
                    continue;
                }
            }

            std::string exportFunction = base::StringPrintf(
                    "function(spec, ...args) { return kaleido_scopes.%s(spec, ...args).then(JSON.stringify); }",
                    scope->ScopeName().c_str());

            std::vector<std::unique_ptr<::headless::runtime::CallArgument>> args = scope->BuildCallArguments();

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
                    base::BindOnce(&Kaleido::OnExportComplete, weak_factory_.GetWeakPtr()));
            // Break out of loop, OnExportComplete callback responsible for calling ExportNext again after this
            // the current request is processed.
            break;
        }
    }
}

void Kaleido::OnExportComplete(
        std::unique_ptr<headless::runtime::CallFunctionOnResult> result) {

    // Make sure the evaluation succeeded before reading the result.
    if (result->HasExceptionDetails()) {
        std::string error = base::StringPrintf(
                "Failed to serialize document: %s", result->GetExceptionDetails()->GetText().c_str());
        kaleido::utils::writeJsonMessage(1, error);
        Reload();
        return;
    } else {
        // JSON parse result to get format
        std::string responseString = result->GetResult()->GetValue()->GetString();
        base::Optional<base::Value> responseJson = base::JSONReader::Read(responseString);
        base::DictionaryValue* responseDict;
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

            devtools_client_->GetPage()->GetExperimental()->PrintToPDF(
                    headless::page::PrintToPDFParams::Builder()
                            .SetMarginBottom(0)
                            .SetMarginTop(0)
                            .SetMarginLeft(0)
                            .SetMarginRight(0)
                            .SetPrintBackground(true)
                            .SetPreferCSSPageSize(true)  // Use @page {size: } CSS style
                            .Build(),
                    base::BindOnce(&Kaleido::OnPDFCreated, weak_factory_.GetWeakPtr(), responseString));
        } else if (format == "emf"){
            // Write SVG data to temporary file
            std::string svgData;
            responseDict->GetString("result", &svgData);

            // Write pdf to temporary file
            std::string inFileName = std::tmpnam(nullptr) + std::string(".svg");
            std::ofstream svgFile;
            svgFile.open(inFileName, std::ios::out);
            svgFile << svgData;
            svgFile.close();

            // Convert pdf to eps temporary file
            std::string outFileName = std::tmpnam(nullptr) + std::string(".emf");
            std::string command = std::string("inkscape --file ") + inFileName + " --export-emf " + outFileName;
            int exitCode = std::system(command.c_str());
            if (exitCode != 0) {
                kaleido::utils::writeJsonMessage(exitCode, "SVG to EMF conversion failed");
                Reload();
                return;
            }

            // Read EMF file as binary
            std::ifstream emfStream(outFileName, std::ios::ate | std::ios::binary);
            std::streamsize size = emfStream.tellg();
            emfStream.seekg(0, std::ios::beg);
            std::vector<uint8_t> emfBuffer(size);
            if (emfStream.read((char*)emfBuffer.data(), size))
            {
                // cleanup temporary files
                std::remove(inFileName.c_str());
                std::remove(outFileName.c_str());

                // Base64 encode EMF data
                std::string base64emf = headless::protocol::Binary::fromVector(emfBuffer).toBase64();

                // Add base64 encoded EMF data to result dict
                responseDict->SetString("result", base64emf);

                // Write results JSON string
                std::string response;
                base::JSONWriter::Write(*responseDict, &response);
                std::cout << response << "\n";

                Reload();
                return;
            } else {
                // cleanup temporary files
                std::remove(inFileName.c_str());
                std::remove(outFileName.c_str());

                kaleido::utils::writeJsonMessage(1, "Failed to read temporary EMF file");
                Reload();
                return;
            }
        } else {
            // Write results json string
            std::cout << result->GetResult()->GetValue()->GetString().c_str() << std::endl;
            Reload();
            return;
        }
    }
}

void Kaleido::Reload() {
    std::unique_ptr<headless::runtime::GetHeapUsageParams> params =
            headless::runtime::GetHeapUsageParams::Builder().Build();
    devtools_client_->GetRuntime()->GetExperimental()->GetHeapUsage(
            std::move(params), base::BindOnce(&Kaleido::OnHeapUsageComplete, weak_factory_.GetWeakPtr()));
}

void Kaleido::OnHeapUsageComplete(std::unique_ptr<headless::runtime::GetHeapUsageResult> result) {
    double heapUsageRatio = result->GetUsedSize() / jsHeapSizeLimit;
    if (heapUsageRatio >= 0.5) {
        // Reload page to clear memory
        std::unique_ptr<headless::page::ReloadParams> params =
        headless::page::ReloadParams::Builder().Build();
        devtools_client_->GetPage()->Reload(std::move(params));
    } else {
        // Memory usage low enough, keep going without reloading page
        ExportNext();
    }
}

void Kaleido::OnHeapEvalComplete(std::unique_ptr<headless::runtime::EvaluateResult> result) {
    if (result->HasExceptionDetails()) {
        std::string error = base::StringPrintf(
                "Failed to get window.performance.memory: %s", result->GetExceptionDetails()->GetText().c_str());
        kaleido::utils::writeJsonMessage(1, error);
        Reload();
        return;
    } else {
        std::string responseString = result->GetResult()->GetValue()->GetString();
        base::Optional<base::Value> responseJson = base::JSONReader::Read(responseString);
        base::DictionaryValue* responseDict;
        responseJson.value().GetAsDictionary(&responseDict);

        // jsHeapSizeLimit
        responseDict->GetDouble("jsHeapSizeLimit", &jsHeapSizeLimit);

        ExportNext();
    }
}

void Kaleido::OnPDFCreated(
        std::string responseString,
        std::unique_ptr<headless::page::PrintToPDFResult> result
) {
    if (!result) {
        std::string error = std::string("Export to PDF failed");
        kaleido::utils::writeJsonMessage(1, error);
    } else {
        base::Optional<base::Value> responseJson = base::JSONReader::Read(responseString);
        base::DictionaryValue* responseDict;
        responseJson.value().GetAsDictionary(&responseDict);

        // format
        std::string format;
        responseDict->GetString("format", &format);

        // Initialize empty result
        std::string stringResult;

        if (format == "eps") {
            // Write pdf to temporary file
            std::string inFileName = std::tmpnam(nullptr) + std::string(".pdf");
            std::ofstream pdfFile;
            pdfFile.open(inFileName, std::ios::out | std::ios::binary);
            pdfFile.write((char*)result->GetData().data(), result->GetData().size());
            pdfFile.close();

            // Convert pdf to eps temporary file
            std::string outFileName = std::tmpnam(nullptr) + std::string(".eps");
            std::string command = std::string("pdftops -eps ") + inFileName + " " + outFileName;
            int exitCode = std::system(command.c_str());
            if (exitCode != 0) {
                kaleido::utils::writeJsonMessage(exitCode, "PDF to EPS conversion failed");
                Reload();
                return;
            }

            // Read EPS file as Text
            std::ifstream epsStream(outFileName, std::ios::in);
            stringResult = std::string((std::istreambuf_iterator<char>(epsStream)),
                                     std::istreambuf_iterator<char>());

            // cleanup temporary files
            std::remove(inFileName.c_str());
            std::remove(outFileName.c_str());
        } else {  // format == "pdf"
            // Add base64 encoded PDF bytes to result dict
            stringResult = result->GetData().toBase64();
        }

        // Add base64 encoded PDF bytes to result dict
        responseDict->SetString("result", stringResult);

        // Write results JSON string
        std::string response;
        base::JSONWriter::Write(*responseDict, &response);
        std::cout << response << "\n";
    }

    Reload();
    return;
}

void Kaleido::OnScriptCompileComplete(
        std::unique_ptr<headless::runtime::CompileScriptResult> result) {
    // Make sure the evaluation succeeded before running script
    if (result->HasExceptionDetails()) {
        LOG(ERROR) << "Failed to compile script: "
                   << result->GetExceptionDetails()->GetText();
    } else {
        std::string plotlyjsScriptId = result->GetScriptId();
        devtools_client_->GetRuntime()->RunScript(
                plotlyjsScriptId,
                base::BindOnce(&Kaleido::OnRunScriptComplete, weak_factory_.GetWeakPtr())
                );
    }
}

void Kaleido::OnRunScriptComplete(
        std::unique_ptr<headless::runtime::RunScriptResult> result) {
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
        kaleido::utils::writeJsonMessage(1, "No Scope Specified");
        browser->Shutdown();
        exit(EXIT_FAILURE);
        return;
    }

    // Get first command line argument as a std::string using a string stream.
    // This handles the case where args[0] is a wchar_t on Windows
    std::stringstream scope_stringstream;
    scope_stringstream << args[0];
    std::string scope_name = scope_stringstream.str();

    // Instantiate renderer scope
    kaleido::scopes::BaseScope *scope = LoadScope(scope_name);

    if (!scope) {
        // Invalid scope name
        kaleido::utils::writeJsonMessage(1,  base::StringPrintf("Invalid scope: %s", scope_name.c_str()));
        browser->Shutdown();
        exit(EXIT_FAILURE);
        return;
    } else if (!scope->errorMessage.empty()) {
        kaleido::utils::writeJsonMessage(1,  scope->errorMessage);
        browser->Shutdown();
        exit(EXIT_FAILURE);
        return;
    }

    // Add javascript bundle
    scope->localScriptFiles.emplace_back("./js/kaleido_scopes.js");

    // Build initial HTML file
    std::list<std::string> scriptTags = scope->ScriptTags();
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
    htmlStringStream << "</head><body style=\"{margin: 0; padding: 0;}\"><img id=\"kaleido-image\"><img></body></html>";

    // Write html to temp file
    std::string tmpFileName = std::tmpnam(nullptr) + std::string(".html");
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

    // Create an instance of Kaleido
    headless::HeadlessWebContents *web_contents = tab_builder.Build();

    // Initialization succeeded
    kaleido::utils::writeJsonMessage(0, "Success");

    // TODO make scope a unique ptr and use move semantics here
    g_example = new Kaleido(browser, web_contents, tmpFileName, scope);
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
