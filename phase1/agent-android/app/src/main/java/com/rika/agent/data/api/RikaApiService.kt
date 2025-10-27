// agent-android/app/src/main/java/com/rika/agent/data/api/RikaApiService.kt
package com.rika.agent.data.api

import com.rika.agent.data.model.*
import retrofit2.http.*

interface RikaApiService {

    @POST("enroll")
    suspend fun enroll(@Body request: EnrollRequest): EnrollResponse

    @POST("enroll/complete")
    suspend fun completeEnrollment(@Body request: EnrollCompleteRequest): EnrollCompleteResponse

    @POST("heartbeat")
    suspend fun sendHeartbeat(
        @Body heartbeat: HeartbeatData,
        @Header("Authorization") authorization: String
    )

    @GET("presence")
    suspend fun getPresence(): PresenceResponse

    @POST("blackout")
    suspend fun triggerBlackout(@Body request: BlackoutRequest)
}