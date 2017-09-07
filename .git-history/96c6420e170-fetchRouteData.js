// @flow
import ExperimentsClient from 'app/common/lib/ExperimentsClient';
import ResourceFactory from 'app/common/lib/ResourceFactory/server';
import type { Metadata } from 'node/lib/Metatags';
import type { RouteDataType } from 'shared/routing/routeDataTypes';

type ResourceResponse = {
  name: string,
  options?: Object,
  response: { data: ?mixed, error: any },
  nextBookmark: string,
};

type MetatagResponse = {
  name: string,
  options?: Object,
  response: { data: Metadata, error: any },
  nextBookmark: string,
};

type Args = {|
  routeData: RouteDataType,
  legacy_server_context: Object,
  params: Object,
  experimentsClients?: {
    experiments: ExperimentsClient,
    seoExperiments: ExperimentsClient,
    seoUnauthExperiments: ExperimentsClient,
  },
|};
/*
* Parallelize prefetch dependencies and the metatag resource
*/
export default async function fetchRouteData({ routeData, legacy_server_context, params, experimentsClients }: Args) {
  const resourceFactory = new ResourceFactory(legacy_server_context, experimentsClients);
  let resourceResponses: ResourceResponse[] = [];
  let dataFetches: Promise<ResourceResponse>[] = [];

  if (!legacy_server_context.app_shell) {
    dataFetches = (routeData.resourceDependencies || []).map(({ name, options }) =>
      resourceFactory.create(name, options).callGet().then(response => ({
        name,
        options,
        response: response.resource_response,
        nextBookmark: response.resource && response.resource.options.bookmarks
          ? response.resource.options.bookmarks[0]
          : '',
      })),
    );
  } else {
    resourceResponses = [];
  }

  let metatagsFetch: Promise<MetatagResponse>;
  if (routeData.metatagResource) {
    const { name, options } = routeData.metatagResource;
    const resource = resourceFactory.create(name, options);
    if (!resource.getPageMetadata) {
      throw new Error(`Resource "${name}" does not support metadata.`);
    }
    metatagsFetch = resource.getPageMetadata().then(response => ({
      name,
      options,
      response: response.resource_response,
      nextBookmark: response.resource && response.resource.options.bookmarks
        ? response.resource.options.bookmarks[0]
        : '',
    }));
  }

  if (!legacy_server_context.app_shell) {
    // Promise.all coerces this to `Object[]`, so we coerce it back here.
    resourceResponses = await Promise.all(dataFetches);
  }
  const metatagsResponse = await metatagsFetch;
  // TODO(jchan): Create a `getSimpleRedirect` which doesn't rely on resource responses so we can signal whether
  // we need to get resources or not on the server.
  const redirect = routeData.getRedirect(legacy_server_context, params, resourceResponses, metatagsResponse);
  return { resourceResponses, metatagsResponse, redirect };
}
