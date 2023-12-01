import type { ElementType, FC, ReactNode } from 'react';

interface CardProps {
	children: ReactNode;
	as?: ElementType;
}

export const Card: FC<CardProps> = ({ children, as: Tag = 'div' }) => {
	return (
		<Tag className={'drop-shadow-md rounded-xl border border-gray-200 bg-white p-4 m-4'}>
			{children}
		</Tag>
	);
};
