package com.localfirst.lifediary;

import android.app.Activity;
import android.os.Bundle;

import org.qtproject.qt.android.bindings.QtActivity;

public class LifeDiaryActivity extends QtActivity {
    private static Activity activity;

    public static Activity currentActivity() {
        return activity;
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        activity = this;
        super.onCreate(savedInstanceState);
    }

    @Override
    protected void onDestroy() {
        if (activity == this) {
            activity = null;
        }
        super.onDestroy();
    }
}
