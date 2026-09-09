#include "ZoomEffect.hpp"

using namespace CrowdControl::Enums;

namespace CrowdControl::Effects {
	EffectStatus ZoomEffect::Test(Request request)
	{
		_LOG_INIT;

		_LOG("ZoomEffect::Test()" << std::endl);

		if (!CanStart(&EffectList::AllEffects))
			return EffectStatus::Retry;

		return EffectStatus::Success;
	}


	EffectStatus ZoomEffect::Start(Request request)
	{
		_LOG_INIT;

		_LOG("ZoomEffect::Start()" << std::endl);

		if (!CanStart(&EffectList::AllEffects))
			return EffectStatus::Retry;

		auto rootObject = ObjectUtil::GetRootObject();
		rootObject->scale = factor;

		SetDuration(request);
		running = true;

		return EffectStatus::Success;
	}

	EffectStatus ZoomEffect::Stop()
	{
		_LOG_INIT;

		_LOG("ZoomEffect::Stop()" << std::endl);

		auto rootObject = ObjectUtil::GetRootObject();
		rootObject->scale = 1.0f;

		running = false;

		return EffectStatus::Success;
	}
}