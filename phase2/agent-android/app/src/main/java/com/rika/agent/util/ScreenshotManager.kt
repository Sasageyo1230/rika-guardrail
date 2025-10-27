// agent-android/app/src/main/java/com/rika/agent/util/ScreenshotManager.kt
package com.rika.agent.util

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.Image
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Handler
import android.os.Looper
import android.util.DisplayMetrics
import android.view.WindowManager
import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer

class ScreenshotManager(private val context: Context) {
    
    companion object {
        private const val SCREENSHOT_REQUEST_CODE = 1001
    }
    
    private var mediaProjectionManager: MediaProjectionManager? = null
    private var mediaProjection: MediaProjection? = null
    private var imageReader: ImageReader? = null
    private var virtualDisplay: VirtualDisplay? = null
    
    init {
        mediaProjectionManager = context.getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
    }
    
    fun hasPermission(): Boolean {
        // In a real implementation, you'd check if we have MediaProjection permission
        // For this skeleton, we'll return true and handle the permission request in the UI
        return true
    }
    
    fun requestPermission(): Intent? {
        return mediaProjectionManager?.createScreenCaptureIntent()
    }
    
    fun setupMediaProjection(resultCode: Int, data: Intent?) {
        if (resultCode == Activity.RESULT_OK && data != null) {
            mediaProjection = mediaProjectionManager?.getMediaProjection(resultCode, data)
            setupImageReader()
        }
    }
    
    private fun setupImageReader() {
        val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
        val displayMetrics = DisplayMetrics()
        windowManager.defaultDisplay.getMetrics(displayMetrics)
        
        val width = displayMetrics.widthPixels
        val height = displayMetrics.heightPixels
        val density = displayMetrics.densityDpi
        
        // Create thumbnail size (400x300 max, maintaining aspect ratio)
        val aspectRatio = width.toFloat() / height.toFloat()
        val thumbnailWidth: Int
        val thumbnailHeight: Int
        
        if (aspectRatio > 4f/3f) {
            thumbnailWidth = 400
            thumbnailHeight = (400 / aspectRatio).toInt()
        } else {
            thumbnailHeight = 300
            thumbnailWidth = (300 * aspectRatio).toInt()
        }
        
        imageReader = ImageReader.newInstance(thumbnailWidth, thumbnailHeight, PixelFormat.RGBA_8888, 1)
        
        virtualDisplay = mediaProjection?.createVirtualDisplay(
            "RikaScreenCapture",
            thumbnailWidth,
            thumbnailHeight,
            density,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            imageReader?.surface,
            null,
            null
        )
    }
    
    suspend fun captureScreenshot(): ByteArray? {
        return try {
            imageReader?.let { reader ->
                val image = reader.acquireLatestImage()
                if (image != null) {
                    val bitmap = imageToBitmap(image)
                    image.close()
                    
                    if (bitmap != null) {
                        bitmapToByteArray(bitmap)
                    } else null
                } else null
            }
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }
    
    private fun imageToBitmap(image: Image): Bitmap? {
        return try {
            val planes = image.planes
            val buffer = planes[0].buffer
            val pixelStride = planes[0].pixelStride
            val rowStride = planes[0].rowStride
            val rowPadding = rowStride - pixelStride * image.width
            
            val bitmap = Bitmap.createBitmap(
                image.width + rowPadding / pixelStride,
                image.height,
                Bitmap.Config.ARGB_8888
            )
            bitmap.copyPixelsFromBuffer(buffer)
            
            // Crop to remove padding if necessary
            if (rowPadding == 0) {
                bitmap
            } else {
                Bitmap.createBitmap(bitmap, 0, 0, image.width, image.height)
            }
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }
    
    private fun bitmapToByteArray(bitmap: Bitmap): ByteArray {
        val stream = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, 85, stream)
        return stream.toByteArray()
    }
    
    fun cleanup() {
        virtualDisplay?.release()
        imageReader?.close()
        mediaProjection?.stop()
        
        virtualDisplay = null
        imageReader = null
        mediaProjection = null
    }
}