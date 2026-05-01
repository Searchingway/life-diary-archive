package com.localfirst.lifediary;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.webkit.MimeTypeMap;

import androidx.core.content.FileProvider;

import java.io.File;

public final class LifeDiaryShare {
    private LifeDiaryShare() {
    }

    public static boolean shareZip(String filePath) {
        Activity activity = LifeDiaryActivity.currentActivity();
        if (activity == null || filePath == null || filePath.length() == 0) {
            return false;
        }

        File file = new File(filePath);
        if (!file.exists() || !file.isFile()) {
            return false;
        }

        Context context = activity.getApplicationContext();
        String authority = context.getPackageName() + ".fileprovider";
        Uri uri = FileProvider.getUriForFile(context, authority, file);

        Intent sendIntent = new Intent(Intent.ACTION_SEND);
        sendIntent.setType(resolveMime(file));
        sendIntent.putExtra(Intent.EXTRA_STREAM, uri);
        sendIntent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        sendIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);

        Intent chooser = Intent.createChooser(sendIntent, "分享人生档案数据包");
        chooser.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        activity.startActivity(chooser);
        return true;
    }

    private static String resolveMime(File file) {
        String extension = MimeTypeMap.getFileExtensionFromUrl(file.getName());
        String mime = MimeTypeMap.getSingleton().getMimeTypeFromExtension(extension);
        if (mime == null || mime.length() == 0) {
            return "application/zip";
        }
        if ("application/x-zip-compressed".equals(mime)) {
            return "application/zip";
        }
        return mime;
    }
}
