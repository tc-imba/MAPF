//
// Created by liu on 24/5/2020.
//

#include <vector>
#include <random>
#include <iostream>
#include <fstream>
#include <algorithm>
#include <sstream>

#include "../solver/Manager.h"
#include "../solver/Solver.h"
#include "../utils/ezOptionParser.hpp"

using namespace std;


string generateMap(const string &dataPath, size_t deliveryWidth, size_t deliveryX, size_t deliveryY, size_t maxX,
                   size_t maxY) {
    string mapName = "well-formed-" + to_string(maxX) + "-" + to_string(maxY);
    ofstream fout(dataPath + "/map/" + mapName + ".map");
    fout << "type octile" << endl
         << "height " << maxX << endl
         << "width " << maxY << endl
         << "map" << endl;

    for (int i = 0; i < maxX; i++) {
        for (int j = 0; j < maxY; j++) {
            if (i % 4 == 2 && j >= 7 && (j - 7) % (deliveryWidth + 1) != deliveryWidth && j < maxY - 7) {
                fout << "@";
            } else {
                fout << ".";
            }
        }
        fout << endl;
    }
    fout.close();

    return mapName;
}

size_t calculateDistance(Solver &solver) {
    size_t count = 0;
    while (!solver.success() && solver.step() && count < 100000) {
        ++count;
    }
    if (!solver.success()) {
        throw runtime_error("solver error");
    }
    auto path = solver.constructPath();
    return path[0]->leaveTime;
}


int main(int argc, const char *argv[]) {
    ez::ezOptionParser optionParser;

    optionParser.overview = "Multi Agent Path Finding Well Formed Task Generation";
    optionParser.syntax = "./MAPF-generate-well-formed [OPTIONS]";
    optionParser.example = "./MAPF-generate-well-formed";
    optionParser.footer = "";

    optionParser.add("5489", false, 1, 0, "Random Seed", "-s", "--seed");
    optionParser.add("10", false, 1, 0, "Agent Number", "-a", "--agent");
    optionParser.add("2", false, 1, 0, "Task Number Per Agent", "-k", "--agent-per-task");
    optionParser.add("", false, 0, 0, "Generate Release Time", "-r", "--release");

    optionParser.add("5", false, 1, 0, "X Grid", "-x");
    optionParser.add("2", false, 1, 0, "Y Grid", "-y");

    optionParser.parse(argc, argv);

    unsigned long agentNum, k, deliveryX, deliveryY, seed;
    bool release;

    optionParser.get("--seed")->getULong(seed);
    optionParser.get("--agent")->getULong(agentNum);
    optionParser.get("--agent-per-task")->getULong(k);
    optionParser.get("-x")->getULong(deliveryX);
    optionParser.get("-y")->getULong(deliveryY);
    release = optionParser.isSet("--release");


    string dataPath = "test-benchmark";

    size_t deliveryWidth = 10;
//    size_t deliveryX = 8;
//    size_t deliveryY = 3;
    size_t maxX = 4 * deliveryX + 1;
    size_t maxY = deliveryY * (deliveryWidth + 1) + 13;

    string mapName = generateMap(dataPath, deliveryWidth, deliveryX, deliveryY, maxX, maxY);

    string filename = dataPath + "/task/" + mapName + "-" + to_string(agentNum) + "-" + to_string(k) + "-" + to_string(seed);
    if (release) {
        filename += "-release";
    }
    filename += ".task";
    cout << filename << endl;
    ofstream fout(filename);

    std::mt19937 g(seed);

    vector<pair<size_t, size_t> > parkingPoints;
    vector<size_t> parkingY = {1, 2, 4, 5, maxY - 6, maxY - 5, maxY - 3, maxY - 2};
    for (size_t i = 1; i < maxX - 1; i++) {
        for (size_t j : parkingY) {
//            cout << i << " " << j << endl;
            parkingPoints.emplace_back(i, j);
        }
    }
    std::shuffle(parkingPoints.begin(), parkingPoints.end(), g);
    cout << "parking: " << parkingPoints.size() << endl;

    vector<pair<size_t, size_t> > taskPoints;
    for (size_t i = 1; i < maxX; i += 2) {
        for (size_t j = 7; j < maxY - 7; j++) {
            if ((j - 7) % (deliveryWidth + 1) != deliveryWidth) {
//                cout << i << " " << j << endl;
                taskPoints.emplace_back(i, j);
            }
        }
    }

    cout << "task: " << taskPoints.size() << endl;
    std::uniform_int_distribution<> sampleTask(0, taskPoints.size() - 1);

    Manager manager(dataPath);
    auto map = manager.getMap(mapName + ".map");

    ostringstream agentConfigs;
    ostringstream taskConfigs;
    Solver solver(map);

    for (size_t i = 0; i < agentNum; i++) {
        auto firstPoint = parkingPoints.back();
        parkingPoints.pop_back();
        agentConfigs << firstPoint.first << " " << firstPoint.second << endl;
        size_t dist = 0;
        int startTime = 0;

        for (size_t j = 0; j < k; j++) {
            auto evenPoint = taskPoints[sampleTask(g)];
            auto scenario = Scenario(i, map, firstPoint, evenPoint, 0, 0);
            solver.initScenario(&scenario);
            dist += calculateDistance(solver);

            auto oddPoint = taskPoints[sampleTask(g)];
            scenario = Scenario(i, map, evenPoint, oddPoint, 0, 0);
            solver.initScenario(&scenario);
            dist += calculateDistance(solver);


            taskConfigs << evenPoint.first << " " << evenPoint.second << " "
                        << oddPoint.first << " " << oddPoint.second << " " << dist << " " << startTime << endl;

            firstPoint = oddPoint;
            if (release) {
                startTime += dist;
            }
        }
    }

    fout << agentNum << " " << k << endl;
    fout << mapName << ".map" << endl;
    fout << agentConfigs.str();
    fout << taskConfigs.str();

    fout.close();

    return 0;
}
