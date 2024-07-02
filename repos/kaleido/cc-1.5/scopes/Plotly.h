//
// Created by jmmease on 6/17/20.
//
#include "Base.h"
#include "base/bind.h"
#include "base/command_line.h"
#include "base/strings/string_util.h"
#include "base/strings/stringprintf.h"
#include "headless/public/devtools/domains/runtime.h"
#include "../utils.h"
#include <streambuf>
#include <string>
#include <sstream>
#include <iostream>
#include <fstream>

#ifndef CHROMIUM_PLOTLYSCOPE_H
#define CHROMIUM_PLOTLYSCOPE_H

namespace kaleido {
    namespace scopes {

        class PlotlyScope : public BaseScope {
        public:
            PlotlyScope();

            ~PlotlyScope() override;

            PlotlyScope(const PlotlyScope &v);

            std::string ScopeName() override;

            std::vector<std::unique_ptr<::headless::runtime::CallArgument>> BuildCallArguments() override;

        public:
            std::string topojsonUrl;
            std::string mapboxToken;
        };

        PlotlyScope::PlotlyScope() : topojsonUrl(), mapboxToken() {
            // Add MathJax config
            scriptTags.emplace_back("window.PlotlyConfig = {MathJaxConfig: 'local'}");

            // Process plotlyjs
            if (HasCommandLineSwitch("plotlyjs")) {
                std::string plotlyjsArg = GetCommandLineSwitch("plotlyjs");

                // Check if value is a URL
                GURL plotlyjsUrl(plotlyjsArg);
                if (plotlyjsUrl.is_valid()) {
                    scriptTags.push_back(plotlyjsArg);
                } else {
                    // Check if this is a local file path
                    if (std::ifstream(plotlyjsArg)) {
                        localScriptFiles.emplace_back(plotlyjsArg);
                    } else {
                        errorMessage = base::StringPrintf("--plotlyjs argument is not a valid URL or file path: %s",
                                                          plotlyjsArg.c_str());
                        return;
                    }
                }
            } else {
                scriptTags.emplace_back("https://cdn.plot.ly/plotly-latest.min.js");
            }

            // MathJax
            if (HasCommandLineSwitch("mathjax")) {
                std::string mathjaxArg = GetCommandLineSwitch("mathjax");

                GURL mathjaxUrl(mathjaxArg);
                if (mathjaxUrl.is_valid()) {
                    std::stringstream mathjaxStringStream;
                    mathjaxStringStream << mathjaxArg << "?config=TeX-AMS-MML_SVG";
                    scriptTags.push_back(mathjaxStringStream.str());
                } else {
                    errorMessage = base::StringPrintf("--mathjax argument is not a valid URL: %s", mathjaxArg.c_str());
                    return;
                }
            }

            // Topojson
            if (HasCommandLineSwitch("topojson")) {
                std::string topojsonArg = GetCommandLineSwitch("topojson");
                if (GURL(topojsonArg).is_valid()) {
                    topojsonUrl = topojsonArg;
                } else {
                    errorMessage = base::StringPrintf("--topojson argument is not a valid URL: %s",
                                                      topojsonArg.c_str());
                    return;
                }
            }

            // Process mapbox-token
            if (HasCommandLineSwitch("mapbox-access-token")) {
                mapboxToken = GetCommandLineSwitch("mapbox-access-token");
            }
        }

        PlotlyScope::~PlotlyScope() {}

        PlotlyScope::PlotlyScope(const PlotlyScope &v) : topojsonUrl(v.topojsonUrl), mapboxToken(v.mapboxToken) {}

        std::string PlotlyScope::ScopeName() {
            return "plotly";
        }

        std::vector<std::unique_ptr<::headless::runtime::CallArgument>> PlotlyScope::BuildCallArguments() {
            std::vector<std::unique_ptr<::headless::runtime::CallArgument>> args;

            // Add mapbox token from command line
            args.push_back(
                    headless::runtime::CallArgument::Builder()
                            .SetValue(std::make_unique<base::Value>(base::StringPiece(mapboxToken)))
                            .Build()
            );

            // Add topojson url from command-line
            args.push_back(
                    headless::runtime::CallArgument::Builder()
                            .SetValue(std::make_unique<base::Value>(base::StringPiece(topojsonUrl)))
                            .Build()
            );
            return args;
        }
    }
}

#endif //CHROMIUM_PLOTLYSCOPE_H
