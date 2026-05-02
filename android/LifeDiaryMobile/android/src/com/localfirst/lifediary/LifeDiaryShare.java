package com.localfirst.lifediary;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.net.Uri;
import android.os.Looper;
import android.util.Log;

import androidx.core.content.FileProvider;

import java.io.File;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

public final class LifeDiaryShare {
    private static final String TAG = "LifeDiaryShare";
    private static final String SHARE_MIME = "application/zip";
    private static volatile String lastError = "";

    private LifeDiaryShare() {
    }

    public static boolean shareZip(String filePath) {
        lastError = "";

        Activity activity = LifeDiaryActivity.currentActivity();
        if (activity == null) {
            return fail("shareZip failed: current Activity is null", null, "\u6ca1\u6709 Activity\uff0c\u65e0\u6cd5\u8c03\u8d77\u5206\u4eab\u9762\u677f");
        }
        if (filePath == null || filePath.length() == 0) {
            return fail("shareZip failed: filePath is empty", null, "\u5206\u4eab\u6587\u4ef6\u8def\u5f84\u65e0\u6548");
        }

        File file = new File(filePath);
        Log.i(TAG, "ZIP path: " + file.getAbsolutePath());
        Log.i(TAG, "ZIP exists: " + file.exists());
        Log.i(TAG, "ZIP size: " + file.length());
        if (!file.exists() || !file.isFile() || file.length() <= 0) {
            return fail("shareZip failed: backup file is missing or empty", null, "\u5907\u4efd\u6587\u4ef6\u751f\u6210\u5931\u8d25");
        }

        Context context = activity;
        String authority = context.getPackageName() + ".fileprovider";
        Log.i(TAG, "FileProvider authority: " + authority);

        Uri uri;
        try {
            uri = FileProvider.getUriForFile(context, authority, file);
        } catch (IllegalArgumentException exception) {
            return fail("shareZip failed: FileProvider URI creation failed", exception, "\u5206\u4eab\u6587\u4ef6\u6388\u6743\u5931\u8d25");
        } catch (SecurityException exception) {
            return fail("shareZip failed: FileProvider security failure", exception, "\u5206\u4eab\u6587\u4ef6\u6388\u6743\u5931\u8d25");
        } catch (Exception exception) {
            return fail("shareZip failed: unexpected FileProvider failure", exception, "\u5206\u4eab\u6587\u4ef6\u6388\u6743\u5931\u8d25");
        }
        Log.i(TAG, "content Uri: " + uri);

        Intent sendIntent = new Intent(Intent.ACTION_SEND);
        sendIntent.setType(SHARE_MIME);
        sendIntent.putExtra(Intent.EXTRA_STREAM, uri);
        sendIntent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        sendIntent.setClipData(ClipData.newUri(context.getContentResolver(), "LifeDiary Backup", uri));
        Log.i(TAG, "Share MIME type: " + SHARE_MIME);

        Intent chooser = Intent.createChooser(sendIntent, "\u5206\u4eab\u4eba\u751f\u6863\u6848\u5907\u4efd\u6570\u636e\u5305");
        chooser.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        chooser.setClipData(ClipData.newUri(context.getContentResolver(), "LifeDiary Backup", uri));

        grantUriPermissions(context, sendIntent, uri);

        return startChooser(activity, chooser);
    }

    public static String lastShareError() {
        return lastError;
    }

    private static boolean startChooser(Activity activity, Intent chooser) {
        if (Looper.myLooper() == Looper.getMainLooper()) {
            return startChooserNow(activity, chooser);
        }

        CountDownLatch latch = new CountDownLatch(1);
        boolean[] result = new boolean[] { false };
        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                try {
                    result[0] = startChooserNow(activity, chooser);
                } finally {
                    latch.countDown();
                }
            }
        });

        try {
            if (!latch.await(5, TimeUnit.SECONDS)) {
                return fail("shareZip failed: startActivity timed out", null, "\u5206\u4eab\u9762\u677f\u8c03\u8d77\u8d85\u65f6");
            }
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            return fail("shareZip failed: interrupted while starting chooser", exception, "\u5206\u4eab\u9762\u677f\u8c03\u8d77\u4e2d\u65ad");
        }
        return result[0];
    }

    private static boolean startChooserNow(Activity activity, Intent chooser) {
        try {
            activity.startActivity(chooser);
            Log.i(TAG, "Share chooser started");
            return true;
        } catch (ActivityNotFoundException exception) {
            return fail("shareZip failed: no activity can handle chooser", exception, "\u6ca1\u6709\u53ef\u7528\u5206\u4eab\u5e94\u7528");
        } catch (SecurityException exception) {
            return fail("shareZip failed: startActivity security failure", exception, "\u5206\u4eab\u6587\u4ef6\u6388\u6743\u5931\u8d25");
        } catch (Exception exception) {
            return fail("shareZip failed: startActivity failed", exception, "startActivity \u5931\u8d25");
        }
    }

    private static void grantUriPermissions(Context context, Intent intent, Uri uri) {
        try {
            PackageManager packageManager = context.getPackageManager();
            List<ResolveInfo> targets = packageManager.queryIntentActivities(intent, PackageManager.MATCH_DEFAULT_ONLY);
            for (ResolveInfo target : targets) {
                if (target.activityInfo == null || target.activityInfo.packageName == null) {
                    continue;
                }
                context.grantUriPermission(
                    target.activityInfo.packageName,
                    uri,
                    Intent.FLAG_GRANT_READ_URI_PERMISSION
                );
            }
        } catch (Exception exception) {
            logException("shareZip warning: grantUriPermissions failed", exception);
        }
    }

    private static boolean fail(String logMessage, Throwable throwable, String userMessage) {
        String summary = exceptionSummary(throwable);
        lastError = summary.length() == 0 ? userMessage : userMessage + ": " + summary;
        if (throwable == null) {
            Log.e(TAG, logMessage + ": " + lastError);
        } else {
            logException(logMessage, throwable);
        }
        return false;
    }

    private static String exceptionSummary(Throwable throwable) {
        if (throwable == null) {
            return "";
        }
        String className = throwable.getClass().getName();
        String message = throwable.getMessage();
        if (message == null || message.length() == 0) {
            return className;
        }
        return className + ": " + message;
    }

    private static void logException(String prefix, Throwable throwable) {
        Log.e(TAG, prefix + " exception class: " + throwable.getClass().getName());
        Log.e(TAG, prefix + " exception message: " + throwable.getMessage());
        Log.e(TAG, prefix + " stackTrace", throwable);
    }
}
