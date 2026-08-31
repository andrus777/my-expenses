package com.andrus.myexpenses.data.model

data class CredentialsRequest(
    val email: String,
    val password: String,
)

data class TokenPairDto(
    val access_token: String,
    val refresh_token: String,
)

data class UserDto(
    val id: String,
    val email: String,
    val created_at: String,
    val updated_at: String,
)

data class AuthResponse(
    val user: UserDto,
    val tokens: TokenPairDto,
)

data class TokensResponse(
    val tokens: TokenPairDto,
)

data class UserResponse(
    val user: UserDto,
)

data class ApiErrorBody(
    val code: String,
    val message: String,
)

data class ApiErrorEnvelope(
    val error: ApiErrorBody,
    val request_id: String?,
)
