//
// Created by jmmease on 6/23/20.
//

#include <iostream>
#include <fstream>

#ifndef CHROMIUM_UTILS_H
#define CHROMIUM_UTILS_H

namespace kaleido {
    namespace utils {
        // Load version string
        std::ifstream verStream("version");
        std::string version((
                std::istreambuf_iterator<char>(verStream)),std::istreambuf_iterator<char>());

        void writeJsonMessage(int code, std::string message) {
            std::string error = base::StringPrintf(
                    "{\"code\": %d, \"message\": \"%s\", \"result\": null, \"version\": \"%s\"}\n",
                    code, message.c_str(), version.c_str());
            std::cout << error;
        }
    }
}

#endif //CHROMIUM_UTILS_H
