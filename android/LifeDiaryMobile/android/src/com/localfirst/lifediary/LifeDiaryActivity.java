package com.localfirst.lifediary;

import android.app.Activity;
import android.content.ContentResolver;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Parcelable;
import android.util.Log;

import org.qtproject.qt.android.bindings.QtActivity;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;

public class LifeDiaryActivity extends QtActivity {
    private static final String TAG = "LifeDiaryActivity";
    private static Activity activity;
    private static volatile String pendingImportPath = null;

    public static Activity currentActivity() {
        return activity;
    }

    /**
     * 获取未处理的导入 ZIP 路径（消费一次）
     */
    public static String getPendingImportPath() {
        String path = pendingImportPath;
        pendingImportPath = null; // 消费掉
        return path;
    }

    /**
     * 从 content:// URI 复制 ZIP 到私有临时目录
     * 供 ArchiveStore.cpp 通过 JNI 调用
     */
    public static String copyContentUriToTemp(String uriString) {
        Activity act = activity;
        if (act == null) {
            Log.e(TAG, "copyContentUriToTemp: no activity available");
            return null;
        }
        if (uriString == null || uriString.isEmpty()) {
            Log.e(TAG, "copyContentUriToTemp: uriString is null/empty");
            return null;
        }
        try {
            Uri uri = Uri.parse(uriString);
            Log.i(TAG, "copyContentUriToTemp: " + uri.toString());
            ContentResolver resolver = act.getContentResolver();
            File importDir = new File(act.getCacheDir(), "imports");
            if (!importDir.exists() && !importDir.mkdirs()) {
                Log.e(TAG, "copyContentUriToTemp: cannot create import dir");
                return null;
            }
            File tempFile = new File(importDir, "content_import_" + System.currentTimeMillis() + ".zip");
            try (InputStream is = resolver.openInputStream(uri);
                 FileOutputStream fos = new FileOutputStream(tempFile)) {
                if (is == null) {
                    Log.e(TAG, "copyContentUriToTemp: openInputStream returned null");
                    return null;
                }
                byte[] buf = new byte[65536];
                int len;
                long total = 0;
                while ((len = is.read(buf)) != -1) {
                    fos.write(buf, 0, len);
                    total += len;
                }
                Log.i(TAG, "copyContentUriToTemp: saved to " + tempFile.getAbsolutePath() + " size: " + total);
            }
            return tempFile.getAbsolutePath();
        } catch (Exception e) {
            Log.e(TAG, "copyContentUriToTemp failed: " + e.getMessage(), e);
            return null;
        }
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        activity = this;
        super.onCreate(savedInstanceState);
        handleIncomingIntent(getIntent());
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent); // QtActivity 也需要最新的 intent
        Log.i(TAG, "onNewIntent called, action: " + (intent != null ? intent.getAction() : "null"));
        handleIncomingIntent(intent);
    }

    @Override
    protected void onResume() {
        super.onResume();
        // 如果 app 从后台恢复，检查是否有正在等待处理的 intent
        Intent intent = getIntent();
        if (intent != null && pendingImportPath == null) {
            handleIncomingIntent(intent);
        }
    }

    @Override
    protected void onDestroy() {
        if (activity == this) {
            activity = null;
        }
        super.onDestroy();
    }

    /**
     * 处理来自微信/QQ 的 ZIP 文件打开请求
     */
    private void handleIncomingIntent(Intent intent) {
        if (intent == null) {
            return;
        }

        String action = intent.getAction();
        Log.i(TAG, "handleIncomingIntent action: " + action);

        if (!Intent.ACTION_VIEW.equals(action)) {
            return;
        }

        Uri data = intent.getData();
        if (data == null) {
            // 尝试从 EXTRA_STREAM 获取（某些 App 用 ACTION_SEND 发送 ZIP）
            Parcelable extraStream = intent.getParcelableExtra(Intent.EXTRA_STREAM);
            if (extraStream instanceof Uri) {
                data = (Uri) extraStream;
            }
        }
        if (data == null) {
            Log.w(TAG, "handleIncomingIntent: no data URI in intent");
            return;
        }

        Log.i(TAG, "Received VIEW intent with URI: " + data.toString());
        Log.i(TAG, "URI scheme: " + data.getScheme());

        // 通过 ContentResolver 复制到私有临时目录
        try {
            ContentResolver resolver = getContentResolver();
            File importDir = new File(getCacheDir(), "imports");
            if (!importDir.exists() && !importDir.mkdirs()) {
                Log.e(TAG, "Cannot create import directory: " + importDir.getAbsolutePath());
                return;
            }

            File tempFile = new File(importDir, "incoming_import.zip");
            // 如果已存在同名文件，用时间戳区分
            if (tempFile.exists()) {
                tempFile = new File(importDir, "incoming_import_" + System.currentTimeMillis() + ".zip");
            }

            try (InputStream is = resolver.openInputStream(data);
                 FileOutputStream fos = new FileOutputStream(tempFile)) {
                if (is == null) {
                    Log.e(TAG, "ContentResolver.openInputStream returned null for: " + data);
                    return;
                }
                byte[] buffer = new byte[65536];
                int len;
                long total = 0;
                while ((len = is.read(buffer)) != -1) {
                    fos.write(buffer, 0, len);
                    total += len;
                }
                Log.i(TAG, "Copied incoming ZIP to: " + tempFile.getAbsolutePath() + " size: " + total);
            }

            pendingImportPath = tempFile.getAbsolutePath();
            Log.i(TAG, "Pending import path set: " + pendingImportPath);
        } catch (Exception e) {
            Log.e(TAG, "Failed to copy incoming ZIP: " + e.getMessage(), e);
            pendingImportPath = null;
        }
    }
}
