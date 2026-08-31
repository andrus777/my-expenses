package com.andrus.myexpenses.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface UserDao {
    @Query("SELECT * FROM current_user LIMIT 1")
    fun observe(): Flow<UserEntity?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun save(user: UserEntity)

    @Query("DELETE FROM current_user")
    suspend fun clear()
}
