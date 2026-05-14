package com.localfirst.lifediary;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.os.Looper;
import android.provider.MediaStore;
import android.util.Log;
import android.webkit.MimeTypeMap;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

public final class LifeDiaryShare {
    private static final String TAG = "LifeDiaryShare";
    private static final String DOWNLOADS_FOLDER = "LifeDiary";
    private static volatile String lastError = "";

    private LifeDiaryShare() {
    }

    /**
     * 将 ZIP 保存到 Downloads/LifeDiary/ 并分享
     */
    public static boolean shareZip(String filePath) {
        lastError = "";

        Activity activity = LifeDiaryActivity.currentActivity();
        if (activity == null) {
            return fail("shareZip failed: current Activity is null", null, "没有 Activity，无法调起分享面板");
        }
        if (filePath == null || filePath.length() == 0) {
            return fail("shareZip failed: filePath is empty", null, "分享文件路径无效");
        }

        File sourceFile = new File(filePath);
        Log.i(TAG, "ZIP source path: " + sourceFile.getAbsolutePath());
        Log.i(TAG, "ZIP exists: " + sourceFile.exists());
        Log.i(TAG, "ZIP size: " + sourceFile.length());
        if (!sourceFile.exists() || !sourceFile.isFile() || sourceFile.length() <= 0) {
            return fail("shareZip failed: backup file is missing or empty", null, "备份文件生成失败");
        }

        // 1. 保存到 Downloads/LifeDiary/
        Uri mediaUri = saveToDownloads(activity, sourceFile);
        if (mediaUri == null) {
            return false;
        }
        Log.i(TAG, "MediaStore Uri: " + mediaUri.toString());

        // 2. 分享 MediaStore Uri
        return shareMediaUri(activity, mediaUri);
    }

    /**
     * 保存 ZIP 到系统 Downloads/LifeDiary/ 目录
     * Android 10+ 使用 MediaStore Downloads API
     * Android 9- 使用 Environment.getExternalStoragePublicDirectory
     */
    private static Uri saveToDownloads(Context context, File sourceFile) {
        String fileName = sourceFile.getName();
        // 确保文件名格式为 LifeDiary_Backup_yyyyMMdd_HHmmss.zip
        if (!fileName.startsWith("LifeDiary_Backup_")) {
            fileName = "LifeDiary_Backup_" + System.currentTimeMillis() + ".zip";
        }

        String mimeType = "application/zip";
        long fileSize = sourceFile.length();

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            // Android 10+ 使用 MediaStore.Downloads
            ContentValues values = new ContentValues();
            values.put(MediaStore.Downloads.DISPLAY_NAME, fileName);
            values.put(MediaStore.Downloads.MIME_TYPE, mimeType);
            values.put(MediaStore.Downloads.SIZE, fileSize);
            values.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/" + DOWNLOADS_FOLDER);
            values.put(MediaStore.Downloads.IS_PENDING, 1);

            ContentResolver resolver = context.getContentResolver();
            Uri uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
            if (uri == null) {
                Log.e(TAG, "saveToDownloads failed: MediaStore insert returned null");
                lastError = "无法保存到 Downloads/LifeDiary/";
                return null;
            }
            Log.i(TAG, "MediaStore insert URI: " + uri.toString());

            try (OutputStream out = resolver.openOutputStream(uri)) {
                if (out == null) {
                    Log.e(TAG, "saveToDownloads failed: resolver.openOutputStream null");
                    try { resolver.delete(uri, null, null); } catch (Exception ignored) {}
                    lastError = "无法写入 Downloads/LifeDiary/";
                    return null;
                }
                try (FileInputStream in = new FileInputStream(sourceFile)) {
                    byte[] buffer = new byte[65536];
                    int len;
                    while ((len = in.read(buffer)) != -1) {
                        out.write(buffer, 0, len);
                    }
                }
            } catch (Exception e) {
                // 清理失败的 pending 条目
                try { resolver.delete(uri, null, null); } catch (Exception ignored) {}
                Log.e(TAG, "saveToDownloads failed: write error", e);
                lastError = "写入 Downloads/LifeDiary/ 失败";
                return null;
            }

            // 标记为完成
            values.clear();
            values.put(MediaStore.Downloads.IS_PENDING, 0);
            resolver.update(uri, values, null, null);

            Log.i(TAG, "ZIP saved to Downloads via MediaStore, URI: " + uri);
            return uri;
        } else {
            // Android 9 及以下直接写文件系统
            File downloadsDir = new File(
                Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
                DOWNLOADS_FOLDER
            );
            if (!downloadsDir.exists() && !downloadsDir.mkdirs()) {
                Log.e(TAG, "saveToDownloads failed: cannot create directory");
                lastError = "无法创建 Downloads/LifeDiary/ 目录";
                return null;
            }

            File targetFile = new File(downloadsDir, fileName);
            try (FileInputStream in = new FileInputStream(sourceFile);
                 FileOutputStream out = new FileOutputStream(targetFile)) {
                byte[] buffer = new byte[65536];
                int len;
                while ((len = in.read(buffer)) != -1) {
                    out.write(buffer, 0, len);
                }
            } catch (Exception e) {
                Log.e(TAG, "saveToDownloads failed: file copy error", e);
                lastError = "复制 ZIP 到 Downloads 失败";
                return null;
            }

            Uri fileUri = Uri.fromFile(targetFile);
            Log.i(TAG, "ZIP saved to Downloads directly, URI: " + fileUri);
            return fileUri;
        }
    }

    /**
     * 分享 MediaStore content:// Uri
     */
    private static boolean shareMediaUri(Context context, Uri mediaUri) {
        // 使用 */* 避免微信 QQ 对 application/zip 兼容异常
        String shareMime = "*/*";
        Log.i(TAG, "Share MIME type: " + shareMime);

        Intent sendIntent = new Intent(Intent.ACTION_SEND);
        sendIntent.setType(shareMime);
        sendIntent.putExtra(Intent.EXTRA_STREAM, mediaUri);
        sendIntent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        sendIntent.setClipData(ClipData.newUri(context.getContentResolver(), "LifeDiary Backup", mediaUri));

        Intent chooser = Intent.createChooser(sendIntent, "分享人生档案数据包");

        // 显式授权给已知的目标包
        grantUriPermissions(context, sendIntent, mediaUri);

        return startChooser((Activity) context, chooser);
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
                return fail("shareZip failed: startActivity timed out", null, "分享面板调起超时");
            }
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            return fail("shareZip failed: interrupted while starting chooser", exception, "分享面板调起中断");
        }
        return result[0];
    }

    private static boolean startChooserNow(Activity activity, Intent chooser) {
        try {
            activity.startActivity(chooser);
            Log.i(TAG, "Share chooser started successfully");
            return true;
        } catch (ActivityNotFoundException exception) {
            return fail("shareZip failed: no activity can handle chooser", exception, "没有可用分享应用");
        } catch (SecurityException exception) {
            return fail("shareZip failed: startActivity security failure", exception, "分享文件授权失败");
        } catch (Exception exception) {
            return fail("shareZip failed: startActivity failed", exception, "startActivity 失败");
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
                String pkg = target.activityInfo.packageName;
                context.grantUriPermission(pkg, uri, Intent.FLAG_GRANT_READ_URI_PERMISSION);
                Log.i(TAG, "grantUriPermission to: " + pkg);
            }

            // 额外显式授权给微信/QQ（即使 ResolveInfo 遗漏）
            String[] wechatPkgs = {
                "com.tencent.mm",
                "com.tencent.mobileqq",
                "com.tencent.tim",
            };
            for (String pkg : wechatPkgs) {
                try {
                    context.grantUriPermission(pkg, uri, Intent.FLAG_GRANT_READ_URI_PERMISSION);
                    Log.i(TAG, "grantUriPermission (explicit) to: " + pkg);
                } catch (Exception e) {
                    Log.d(TAG, "grantUriPermission skipped (not installed): " + pkg);
                }
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
