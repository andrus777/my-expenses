package com.andrus.myexpenses.data.local

import androidx.room.Dao
import androidx.room.Query
import androidx.room.Upsert
import kotlinx.coroutines.flow.Flow

@Dao
interface CategoryDao {
    @Query("SELECT * FROM categories WHERE ownerUserId = :ownerId ORDER BY name")
    fun observe(ownerId: String): Flow<List<CategoryEntity>>

    @Upsert
    suspend fun upsertAll(categories: List<CategoryEntity>)

    @Query("DELETE FROM categories WHERE ownerUserId = :ownerId")
    suspend fun clear(ownerId: String)
}
