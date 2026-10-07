package com.example.notes

import androidx.lifecycle.ViewModel

class NotesViewModel : ViewModel() {
    fun count(notes: List<String>): Int = notes.size
}
