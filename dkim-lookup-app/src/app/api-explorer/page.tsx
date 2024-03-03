"use client";

import SwaggerUI from 'swagger-ui-react';
import "swagger-ui-react/swagger-ui.css"

export default async function Page() {
	return <SwaggerUI url="openapi.yaml" />
}
