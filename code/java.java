package com.exteraplugins.shareui_dkta_fixed;

import android.content.Context;
import android.os.PowerManager;
import android.util.Log;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;

public class Main {
    private static final String TAG = "ShareuiDktaFixed";
    private static volatile boolean loaded = false;
    private static volatile boolean enabled = true;
    private static volatile boolean wakeLockEnabled = true;

    private static final List<XC_MethodHook.Unhook> hooks = new ArrayList<XC_MethodHook.Unhook>();
    private static PowerManager.WakeLock wakeLock = null;

    public static synchronized void load() {
        if (loaded) return;
        loaded = true;
        Log.d(TAG, "Loading native hooks...");
        installHooks();
    }

    public static synchronized void unload() {
        Log.d(TAG, "Unloading native hooks...");
        for (XC_MethodHook.Unhook unhook : hooks) {
            try {
                unhook.unhook();
            } catch (Throwable ignored) {}
        }
        hooks.clear();
        releaseWakeLock();
        loaded = false;
    }

    public static void setEnabled(boolean value) {
        enabled = value;
        if (!enabled) {
            releaseWakeLock();
        }
    }

    public static void setWakeLockEnabled(boolean value) {
        wakeLockEnabled = value;
        if (!wakeLockEnabled) {
            releaseWakeLock();
        }
    }

    private static void installHooks() {
        // 1. Hook ChatMessageCell.cancelLoading(MessageObject)
        try {
            Class<?> cmcClass = Class.forName("org.telegram.ui.Cells.ChatMessageCell");
            Class<?> moClass = Class.forName("org.telegram.messenger.MessageObject");
            for (Method m : cmcClass.getDeclaredMethods()) {
                if ("cancelLoading".equals(m.getName())) {
                    Class<?>[] pTypes = m.getParameterTypes();
                    if (pTypes.length == 1 && pTypes[0].isAssignableFrom(moClass)) {
                        m.setAccessible(true);
                        hooks.add(XposedBridge.hookMethod(m, new XC_MethodHook() {
                            @Override
                            public void beforeHookedMethod(MethodHookParam param) {
                                if (!enabled) return;
                                Object msg = param.args[0];
                                if (msg != null) {
                                    try {
                                        Field f = msg.getClass().getDeclaredField("loadingCancelled");
                                        f.setAccessible(true);
                                        boolean isCancelled = f.getBoolean(msg);
                                        if (!isCancelled) {
                                            // Cell detach auto-cancel: block it!
                                            param.setResult(null);
                                        }
                                    } catch (Throwable t) {
                                        param.setResult(null);
                                    }
                                }
                            }
                        }));
                    }
                }
            }
        } catch (Throwable t) {
            Log.e(TAG, "Failed to hook ChatMessageCell.cancelLoading", t);
        }

        // 2. Hook FileLoader.cancelLoadFile to block automatic cancellations from UI
        try {
            Class<?> flClass = Class.forName("org.telegram.messenger.FileLoader");
            for (Method m : flClass.getDeclaredMethods()) {
                if ("cancelLoadFile".equals(m.getName())) {
                    m.setAccessible(true);
                    hooks.add(XposedBridge.hookMethod(m, new XC_MethodHook() {
                        @Override
                        public void beforeHookedMethod(MethodHookParam param) {
                            if (!enabled) return;
                            StackTraceElement[] stack = Thread.currentThread().getStackTrace();
                            if (isAutoCancel(stack)) {
                                param.setResult(null);
                            }
                        }
                    }));
                }
            }
        } catch (Throwable t) {
            Log.e(TAG, "Failed to hook FileLoader.cancelLoadFile", t);
        }

        // 3. Hook FileLoader.changePriority to prevent dropping download priority to 0 (PRIORITY_VALUE_LOW)
        try {
            Class<?> flClass = Class.forName("org.telegram.messenger.FileLoader");
            for (Method m : flClass.getDeclaredMethods()) {
                if ("changePriority".equals(m.getName())) {
                    m.setAccessible(true);
                    hooks.add(XposedBridge.hookMethod(m, new XC_MethodHook() {
                        @Override
                        public void beforeHookedMethod(MethodHookParam param) {
                            if (!enabled) return;
                            try {
                                if (param.args != null && param.args.length > 0 && param.args[0] instanceof Integer) {
                                    int priority = ((Integer) param.args[0]).intValue();
                                    if (priority <= 0) {
                                        // Keep at least normal priority (65536)
                                        param.args[0] = Integer.valueOf(65536);
                                    }
                                }
                            } catch (Throwable ignored) {}
                        }
                    }));
                }
            }
        } catch (Throwable t) {
            Log.e(TAG, "Failed to hook FileLoader.changePriority", t);
        }

        // 4. Hook FileLoader.loadFile to mark MessageObject.putInDownloadsStore = true and acquire wake lock
        try {
            Class<?> flClass = Class.forName("org.telegram.messenger.FileLoader");
            Class<?> moClass = Class.forName("org.telegram.messenger.MessageObject");
            for (Method m : flClass.getDeclaredMethods()) {
                if ("loadFile".equals(m.getName())) {
                    m.setAccessible(true);
                    hooks.add(XposedBridge.hookMethod(m, new XC_MethodHook() {
                        @Override
                        public void beforeHookedMethod(MethodHookParam param) {
                            if (!enabled) return;
                            try {
                                if (param.args != null) {
                                    for (Object arg : param.args) {
                                        if (arg != null && moClass.isAssignableFrom(arg.getClass())) {
                                            Field f = arg.getClass().getDeclaredField("putInDownloadsStore");
                                            f.setAccessible(true);
                                            f.setBoolean(arg, true);
                                        }
                                    }
                                }
                                checkAndAcquireWakeLock();
                            } catch (Throwable ignored) {}
                        }
                    }));
                }
            }
        } catch (Throwable t) {
            Log.e(TAG, "Failed to hook FileLoader.loadFile", t);
        }
    }

    private static boolean isAutoCancel(StackTraceElement[] stack) {
        if (stack == null) return false;
        for (int i = 0; i < Math.min(stack.length, 25); i++) {
            String method = stack[i].getMethodName();
            String cls = stack[i].getClassName();

            // Explicit user actions: allow cancel!
            if ("didPressButton".equals(method) || "didPressMiniButton".equals(method) ||
                cls.contains("SearchDownloadsContainer") || "cancelDownloading".equals(method) ||
                "cancelAll".equals(method)) {
                return false;
            }

            // Automatic UI lifecycle cleanups: BLOCK cancel!
            if ("cancelLoading".equals(method) || "fileDetach".equals(method) ||
                "onPhotoClosed".equals(method) || "switchToNextIndex".equals(method) ||
                "checkImageReceiversAttachState".equals(method) || "onDetachedFromWindow".equals(method) ||
                "onFragmentDestroy".equals(method)) {
                return true;
            }
        }
        return false;
    }

    public static synchronized void checkAndAcquireWakeLock() {
        if (!wakeLockEnabled) return;
        try {
            Class<?> appLoader = Class.forName("org.telegram.messenger.ApplicationLoader");
            Field ctxField = appLoader.getDeclaredField("applicationContext");
            ctxField.setAccessible(true);
            Context ctx = (Context) ctxField.get(null);
            if (ctx == null) return;

            if (wakeLock == null) {
                PowerManager pm = (PowerManager) ctx.getSystemService(Context.POWER_SERVICE);
                if (pm != null) {
                    wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "extera:shareui_dkta_fixed");
                    wakeLock.setReferenceCounted(false);
                }
            }
            if (wakeLock != null && !wakeLock.isHeld()) {
                wakeLock.acquire(15 * 60 * 1000L); // 15 min safe guard
            }
        } catch (Throwable ignored) {}
    }

    public static synchronized void releaseWakeLock() {
        try {
            if (wakeLock != null && wakeLock.isHeld()) {
                wakeLock.release();
            }
        } catch (Throwable ignored) {}
    }
}
