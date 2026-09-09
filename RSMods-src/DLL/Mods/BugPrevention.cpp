#include "BugPrevention.hpp"

namespace BugPrevention {

	/// <summary>
	/// When Rocksmith opens with a Oculus / Meta headset connected to the user computer, it can cause a crash.
	/// This is due to Rocksmith saying it owns memory that it doesn't have access to.
	/// In this fix, we jump over the interior of the for-loop (marked as a while with a break case) that writes to invalid memory.
	/// </summary>
	void PreventOculusCrash() {
		_LOG_INIT;

		MemUtil::PatchAdr((LPVOID)Offsets::ptr_OculusCrashJmp, "\xE9\x19\x02\x00\x00\x90", 6);
		_LOG("(BUG PREVENTION) Prevented Oculus Crash" << std::endl);
	}

	/// <summary>
	/// When the user enters a song with a buggy tone, every tone after it will not work.
	/// This mod prevents that by changing a conditional jump to a jump that always happens.
	/// So when the user encounters a broken tone, all they need to do is change the tone and the tones should start working again.
	/// </summary>
	void PreventStuckTone() {
		_LOG_INIT;

		MemUtil::PatchAdr((LPVOID)Offsets::ptr_StuckToneJmp, "\xEB", 1);
		_LOG("(BUG PREVENTION) Prevented Tone Bug" << std::endl);
	}

	/// <summary>
	/// When a user has a faulty PnP (Plug-n-Play) device connected Rocksmith can crash.
	/// It crashes with a memory access violation. The following code skips over the while loop that may eventually crash.
	/// </summary>
	void PreventPnPCrash() {
		_LOG_INIT;

		MemUtil::PatchAdr((LPVOID)Offsets::ptr_PnpJmp_1, "\xE9\x19\x02\x00\x00\x90", 6);
		MemUtil::PatchAdr((LPVOID)Offsets::ptr_PnpJmp_2, "\x90\x90\x90\x90\x90\x90", 6);
		_LOG("(BUG PREVENTION) Prevented PnP Crash" << std::endl);
	}

	/// <summary>
	/// Ubisoft lets you put almost any character in your Uplay password.
	/// However, Rocksmith does not allow some characters.
	/// This means that the user will have to change their password if they are using an invalid character, and they want to use leaderboards.
	/// Some of those invalid characters are as follows: " \ / and =
	/// This mod prevents the checks for those characters to allow the user to have more complex passwords.
	/// </summary>
	void AllowComplexPasswords() {
		_LOG_INIT;

		MemUtil::PatchAdr((LPVOID)Offsets::ptr_Password_LimitCharacters, "\x90\x90", 2);
		MemUtil::PatchAdr((LPVOID)Offsets::ptr_Password_LimitCharacters_Clipboard, "\x90\x90", 2);

		_LOG("(BUG PREVENTION) Allowed Complex Uplay Passwords" << std::endl);
	}

	void __declspec(naked) advancedDisplayCrashHook()
	{
		__asm {

			cmp ECX, 0 // ECX == NULL?

			je prevAdvancedDisplayCrash // If ECX == NULL, then we need to jump to prevAdvancedDisplayCrash


			mov DL, BYTE PTR DS : [ECX + 0x4]	// The code we are overwriting to place this hook
			push EDI						// The code we are overwriting to place this hook
			MOV EDI, DWORD PTR DS : [ESI + 0xC] // The code we are overwriting to place this hook

			jmp Offsets::ptr_AdvancedDisplayCrashJmpBck // Jump back into the original code.

			prevAdvancedDisplayCrash :
			ret							// ECX is NULL, so we need to leave this function or we will crash.
		}
	}

	/// <summary>
	/// When a user enters their Advanced Display settings, there is a tendency for Rocksmith 2014 to crash.
	/// This mod tries to prevent that by exiting the function if ECX (the memory address it is reading from) is NULL.
	/// </summary>
	void PreventAdvancedDisplayCrash() {
		_LOG_INIT;

		MemUtil::PlaceHook((void*)Offsets::ptr_AdvancedDisplayCrash, advancedDisplayCrashHook, 7);

		FlushInstructionCache(GetCurrentProcess(), (void*)Offsets::ptr_AdvancedDisplayCrash, 7);

		_LOG("(BUG PREVENTION) Prevented Advanced Display Crash" << std::endl);
	}


	/// <summary>
	/// In extremely rare cases, the user may have an audio in device have a driver issue.
	/// This causes Rocksmith to crash when it reads all of their audio input devices.
	/// This just patches out those checks, so it won't crash when EBX is a nullptr.
	/// </summary>
	void PreventPortAudioInDeviceCrash() {
		_LOG_INIT;

		// Overwrite some code that doesn't do null checks with NOP.
		// Be very careful in this code. If you overwrite the next instruction, then you end up breaking audio input.
		// NB: JZ has been replaced by JL, now it's 10 bytes in total
		MemUtil::PatchAdr((LPVOID)Offsets::ptr_PortAudioInCrash, "\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90", 10);

		_LOG("(BUG PREVENTION) Prevented Port Audio In Device Crash" << std::endl);
	}

	/// <summary>
	/// The 10 bytes this hook steals, as they appear in an unmodified Rocksmith2014.exe.
	/// mov edx, dword ptr [esp + 0x10]  /  mov dword ptr [ebx + 0x788], edx
	/// </summary>
	static const unsigned char calibrationSampleCountClampOriginal[10] = {
		0x8B, 0x54, 0x24, 0x10, 0x89, 0x93, 0x88, 0x07, 0x00, 0x00
	};

	/// <summary>
	/// Clamps the sample count to the buffer's real capacity before it is stored.
	/// </summary>
	void __declspec(naked) calibrationSampleCountClampHook() {
		__asm {
			mov edx, dword ptr [esp + 0x10]		// The code we are overwriting to place this hook
			cmp edx, 100						// Capacity of the ring buffer, per player
			jbe keepCalibrationSampleCount
			mov edx, 100
		keepCalibrationSampleCount:
			mov dword ptr [ebx + 0x788], edx	// The code we are overwriting to place this hook

			jmp Offsets::ptr_calibrationSampleCountClampJmpBck	// Return to the code we were running.
		}
	}

	/// <summary>
	/// The input calibration screen sizes its volume averaging buffer to the current framerate (1.0 / delta time),
	/// but the buffer is a fixed 100 floats per player. Above ~100 FPS the sampler writes past the end of it, and
	/// the mean is then taken over more floats than the array holds, reading neighbouring members as if they were
	/// samples. The mean never settles in the acceptance window, so the meter never fills and calibration cannot
	/// be completed - which is why players on high refresh rate displays have to cap their framerate first.
	/// Clamping that count to the real capacity fixes both the writes and the reads. Nothing at or below 100 FPS
	/// changes; above it the averaging window just covers less time.
	///
	/// Ported from RSMods 1.2.8.4. Upstream hooks blindly; this build verifies the 10 bytes it is about to steal
	/// first, because the address cannot be checked ahead of time (Rocksmith2014.exe ships Steam-stub packed, so
	/// .text has no raw data on disk and only exists once the stub has unpacked it into memory).
	/// </summary>
	void FixCalibrationSampleCount() {
		_LOG_INIT;

		if (memcmp((void*)Offsets::ptr_calibrationSampleCountClamp, calibrationSampleCountClampOriginal, sizeof(calibrationSampleCountClampOriginal)) != 0) {
			_LOG_SETLEVEL(LogLevel::Error);
			_LOG("(BUG PREVENTION) Calibration fix SKIPPED - unexpected bytes at the hook site. Wrong game build?" << std::endl);
			_LOG_SETLEVEL(LogSettings::defaultLogLevel);
			return;
		}

		MemUtil::PlaceHook((void*)Offsets::ptr_calibrationSampleCountClamp, calibrationSampleCountClampHook, 10);

		FlushInstructionCache(GetCurrentProcess(), (void*)Offsets::ptr_calibrationSampleCountClamp, 10);

		_LOG("(BUG PREVENTION) Fixed Calibration At High Framerates" << std::endl);
	}
}
