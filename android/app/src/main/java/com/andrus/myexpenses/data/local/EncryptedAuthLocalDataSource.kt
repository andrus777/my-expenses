package com.andrus.myexpenses.data.local

import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import com.andrus.myexpenses.domain.model.AuthTokens
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

class EncryptedAuthLocalDataSource(
    private val dataStore: DataStore<Preferences>,
    private val cipher: TokenCipher,
) : AuthLocalDataSource {
    override val tokens: Flow<AuthTokens?> =
        dataStore.data.map { preferences ->
            val encryptedAccess = preferences[ACCESS_TOKEN] ?: return@map null
            val encryptedRefresh = preferences[REFRESH_TOKEN] ?: return@map null
            runCatching {
                AuthTokens(
                    accessToken = cipher.decrypt(encryptedAccess),
                    refreshToken = cipher.decrypt(encryptedRefresh),
                )
            }.getOrNull()
        }

    override suspend fun currentTokens(): AuthTokens? = tokens.first()

    override suspend fun saveTokens(tokens: AuthTokens) {
        dataStore.edit { preferences ->
            preferences[ACCESS_TOKEN] = cipher.encrypt(tokens.accessToken)
            preferences[REFRESH_TOKEN] = cipher.encrypt(tokens.refreshToken)
        }
    }

    override suspend fun clear() {
        dataStore.edit { it.clear() }
    }

    private companion object {
        val ACCESS_TOKEN = stringPreferencesKey("encrypted_access_token")
        val REFRESH_TOKEN = stringPreferencesKey("encrypted_refresh_token")
    }
}
