// build call arguments is fucked

//
// Created by jmmease on 6/17/20.
//
#ifndef CHROMIUM_PLOTLYSCOPE_H
#define CHROMIUM_PLOTLYSCOPE_H
#include "Base.h"
#include "base/functional/bind.h"
#include "base/command_line.h"
#include "base/strings/string_util.h"
#include "base/strings/stringprintf.h"
#include <streambuf>
#include <string>
#include <sstream>
#include <iostream>
#include <fstream>


namespace kaleido {
    namespace scopes {

        class PlotlyScope : public BaseScope {
        public:
            PlotlyScope();

            ~PlotlyScope() override;

            PlotlyScope(const PlotlyScope &v);

            std::string ScopeName() override;

            base::Value::List BuildCallArguments() override;

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

        base::Value::List PlotlyScope::BuildCallArguments() {

            base::Value::List args;

			base::Value::Dict arg1;
			arg1.Set("value", mapboxToken);
			base::Value::Dict arg2;
			arg2.Set("value", topojsonUrl);

            // Add mapbox token from command line
            args.Append(std::move(arg1));
            args.Append(std::move(arg2));

            // TODO essentially were setting strings to functions
            return args;
        }
    }
}

#endif //CHROMIUM_PLOTLYSCOPE_H
