#ifndef SOCIAL_NETWORK_MICROSERVICES_UTILS_H
#define SOCIAL_NETWORK_MICROSERVICES_UTILS_H

#include <string>
#include <fstream>
#include <iostream>
#include <nlohmann/json.hpp>

#include "logger.h"

namespace social_network{
using json = nlohmann::json;

int load_config_file(const std::string &file_name, json *config_json) {
  std::ifstream json_file;
  json_file.open(file_name);
  if (json_file.is_open()) {
    json_file >> *config_json;
    json_file.close();
    return 0;
  }
  else {
    LOG(error) << "Cannot open service-config.json";
    return -1;
  }
};

int ipPrintWindowInMS = 50; // 50 milliseconds.

int writeHomeTimeline_initObjID = 1;
int writeHomeTimeline_numQueueObjs = 1;

int userTimeline_initObjID = writeHomeTimeline_initObjID + writeHomeTimeline_numQueueObjs;
int userTimeline_numQueueObjs = 2;

int userHandler_initObjID = userTimeline_initObjID + userTimeline_numQueueObjs;
int userHandler_numQueueObjs = 6;

int userMention_initObjID = userHandler_initObjID + userHandler_numQueueObjs;
int userMention_numQueueObjs = 1;

int urlShort_initObjID = userMention_initObjID + userMention_numQueueObjs;
int urlShort_numQueueObjs = 1;

int uniqueId_initObjID = urlShort_initObjID + urlShort_numQueueObjs;
int uniqueId_numQueueObjs = 1;

int text_initObjID = uniqueId_initObjID + uniqueId_numQueueObjs;
int text_numQueueObjs = 1;

int socialGraph_initObjID = text_initObjID + text_numQueueObjs;
int socialGraph_numQueueObjs = 7;

int postStorage_initObjID = socialGraph_initObjID + socialGraph_numQueueObjs;
int postStorage_numQueueObjs = 3;

int media_initObjID = postStorage_initObjID + postStorage_numQueueObjs;
int media_numQueueObjs = 1;

int homeTimeline_initObjID = media_initObjID + media_numQueueObjs;
int homeTimeline_numQueueObjs = 1;

int composePost_initObjID = homeTimeline_initObjID + homeTimeline_numQueueObjs;
int composePost_numQueueObjs = 10;

// Home timeline --begin
int idx_writeHomeTline_write = 0;
// Home timeline --end

// Home timeline --begin
int idx_userTline_ReadUserTimeline = 0;
int idx_userTline_WriteUserTimeline = 1;
// Home timeline --end

// Text --begin
int idx_userHandler_RegisterUserWithId = 0;
int idx_userHandler_RegisterUser = 1;
int idx_userHandler_UploadCreatorWithUsername = 2;

int idx_userHandler_UploadCreatorWithUserId = 3;
int idx_userHandler_Login = 4;
int idx_userHandler_GetUserId = 5;
// Text --end

// Text --begin
int idx_userMention_UploadUserMention = 0;
// Text --end

// Text --begin
int idx_urlShort_UploadUrl = 0;
// Text --end


// uniqueId --begin
int idx_uniqueId_UploadUniqueId = 0;
//int idx_uniqueId_HashMacAddressPid = 1;
//int idx_uniqueId_GetMachineId = 2;
// uniqueId --end

// Text --begin
int idx_text_UploadText = 0;
// Text --end

// socialGraph --begin
int idx_socialGraph_follow = 0;
int idx_socialGraph_unfollow = 1;
int idx_socialGraph_getFollowers = 2;
int idx_socialGraph_getFollowees = 3;
int idx_socialGraph_insertUser = 4;

int idx_socialGraph_followWithUsername = 5;
int idx_socialGraph_unfollowWithUsername = 6;
// socialGraph --end

// postStorage --begin
int idx_postStorage_storePost = 0;
int idx_postStorage_readPost = 1;
int idx_postStorage_readMultiplePosts = 2;
// postStorage --end

// Media --begin
int idx_media_UploadMedia = 0;
// Media --end

// Home timeline --begin
int idx_homeTline_ReadHomeTimeline = 0;
// Home timeline --end

// Compose post --begin
// offsets for all the compose objects.
int idx_ComposePost_UploadCreator = 0;  // UploadCreator
int idx_ComposePost_UploadText = 1;  // UploadText
int idx_ComposePost_UploadMedia = 2;  // UploadMedia
int idx_ComposePost_UploadUniqueId = 3;  // UploadUniqueId
int idx_ComposePost_UploadUrls = 4;  // UploadUrls

int idx_ComposePost_UploadUserMentions = 5;  // UploadUserMentions
int idx_ComposePost_ComposeAndUpload = 6;  // _ComposeAndUpload
int idx_ComposePost_UploadPostHelper = 7;  // _UploadPostHelper
int idx_ComposePost_UploadUserTimelineHelper = 8;  // _UploadUserTimelineHelper
int idx_ComposePost_UploadHomeTimelineHelper = 9;  // _UploadHomeTimelineHelper
// Compose post --end


} //namespace social_network

#endif //SOCIAL_NETWORK_MICROSERVICES_UTILS_H
