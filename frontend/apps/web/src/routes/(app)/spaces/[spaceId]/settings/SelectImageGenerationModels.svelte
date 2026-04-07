<!--
    Copyright (c) 2024 Sundsvalls Kommun

    Licensed under the MIT License.
-->

<script lang="ts">
  import { getSpacesManager } from "$lib/features/spaces/SpacesManager";
  import type { ImageGenerationModel } from "@intric/intric-js";
  import ModelNameAndVendor from "$lib/features/ai-models/components/ModelNameAndVendor.svelte";
  import { Input, Tooltip } from "@intric/ui";
  import { derived } from "svelte/store";
  import { Settings } from "$lib/components/layout";
  import { sortModels } from "$lib/features/ai-models/sortModels";
  import { m } from "$lib/paraglide/messages";
  import { toast } from "$lib/components/toast";

  export let selectableModels: (ImageGenerationModel & {
    meets_security_classification?: boolean | null | undefined;
  })[];
  sortModels(selectableModels);

  const {
    state: { currentSpace },
    updateSpace
  } = getSpacesManager();

  const currentlySelectedModels = derived(
    currentSpace,
    ($currentSpace) => $currentSpace.image_generation_models?.map((model) => model.id) ?? []
  );

  let loading = new Set<string>();

  async function toggleModel(model: ImageGenerationModel) {
    loading.add(model.id);
    loading = loading;

    try {
      if ($currentlySelectedModels.includes(model.id)) {
        const newModels = $currentlySelectedModels
          .filter((id) => id !== model.id)
          .map((id) => {
            return { id };
          });
        await updateSpace({ image_generation_models: newModels });
      } else {
        const newModels = [...$currentlySelectedModels, model.id].map((id) => {
          return { id };
        });
        await updateSpace({ image_generation_models: newModels });
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : String(e));
    }
    loading.delete(model.id);
    loading = loading;
  }
</script>

<Settings.Row
  title={m.image_generation_models()}
  description={m.image_generation_models_description()}
>
  {#each selectableModels as model (model.id)}
    {@const meetsClassification = model.meets_security_classification ?? true}
    <Tooltip
      text={meetsClassification ? undefined : m.model_does_not_meet_security_classification()}
    >
      <div
        class="border-default hover:bg-hover-dimmer cursor-pointer border-b py-4 pr-4 pl-2"
        class:pointer-events-none={!meetsClassification}
        class:opacity-60={!meetsClassification}
      >
        <Input.Switch
          value={$currentlySelectedModels.includes(model.id)}
          sideEffect={() => {
            if (meetsClassification) {
              toggleModel(model);
            }
          }}
        >
          <ModelNameAndVendor {model} />
        </Input.Switch>
      </div>
    </Tooltip>
  {/each}
</Settings.Row>
